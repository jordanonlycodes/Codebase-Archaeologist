import io
from pathlib import Path
from tempfile import TemporaryDirectory as RealTemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import analysis


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_dashboard_and_assets(client):
    response = client.get("/explore")
    assert response.status_code == 200
    assert "Bring the source." in response.text
    assert 'id="analyze-zip"' in response.text and 'id="github-url"' in response.text
    assert response.headers["cache-control"] == "no-store"
    for path in ["/static/product/design.css", "/static/product/workspace.js", "/static/mark.svg", "/docs", "/openapi.json", "/api/health"]:
        assert client.get(path).status_code == 200


def test_successful_zip_analysis(client, make_zip, sample_files):
    response = client.post("/api/analyze", files={"file": ("example.zip", make_zip(sample_files), "application/zip")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"]["files"] == 4
    assert data["summary"]["source_lines"] == 6
    assert data["summary"]["total_lines"] == sum(file["lines"] for file in data["files"])
    assert data["summary"]["bytes"] == sum(file["bytes"] for file in data["files"])
    assert data["schema_version"] == "1.0"
    assert "prediction" not in data and "risk_score" not in data


@pytest.mark.parametrize("filename,body,status", [("bad.zip", b"garbage", 400), ("code.py", b"x=1", 415), ("empty.zip", b"", 400)])
def test_invalid_upload(client, filename, body, status):
    response = client.post("/api/analyze", files={"file": (filename, body)})
    assert response.status_code == status
    assert response.json()["error"]["message"]


def test_missing_file(client):
    response = client.post("/api/analyze", files={"wrong": ("repo.zip", b"bad")})
    assert response.status_code == 422


def test_non_multipart(client):
    response = client.post("/api/analyze", json={"url": "https://github.com/example/repo"})
    assert response.status_code == 415


def test_multiple_files(client, make_zip):
    data = make_zip({"a.py": "x=1"}).getvalue()
    response = client.post("/api/analyze", files=[("file", ("a.zip", data)), ("file", ("b.zip", data))])
    assert response.status_code == 400


def test_body_limit_before_multipart(client):
    response = client.post("/api/analyze", content=b"small", headers={"content-length": str(27 * 1024 * 1024)})
    assert response.status_code == 413


def test_oversized_filename(client, make_zip):
    response = client.post("/api/analyze", files={"file": ("x" * 256 + ".zip", make_zip({"a.py": "x=1"}))})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_filename"


@pytest.mark.parametrize("malicious", [False, True])
def test_temporary_files_removed_on_success_and_failure(client, make_zip, tmp_path, monkeypatch, malicious):
    created = []
    def temporary_directory(**kwargs):
        directory = RealTemporaryDirectory(dir=tmp_path, **kwargs)
        created.append(Path(directory.name))
        return directory
    monkeypatch.setattr(analysis, "TemporaryDirectory", temporary_directory)
    data = make_zip({"../bad.py" if malicious else "main.py": "x=1"})
    response = client.post("/api/analyze", files={"file": ("repo.zip", data)})
    assert response.status_code == (400 if malicious else 200)
    assert created and all(not path.exists() for path in created)


def test_cleanup_on_corrupt_entry_after_partial_extraction(client, make_zip, tmp_path, monkeypatch):
    created = []
    def temporary_directory(**kwargs):
        directory = RealTemporaryDirectory(dir=tmp_path, **kwargs)
        created.append(Path(directory.name))
        return directory
    monkeypatch.setattr(analysis, "TemporaryDirectory", temporary_directory)
    data = make_zip({"a.py": "valid", "b.py": "corruptme"}).getvalue().replace(b"corruptme", b"corruptXX")
    response = client.post("/api/analyze", files={"file": ("repo.zip", io.BytesIO(data))})
    assert response.status_code == 400
    assert created and all(not path.exists() for path in created)
