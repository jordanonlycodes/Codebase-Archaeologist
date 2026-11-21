from dataclasses import asdict

import pytest

from app.analysis.lines import measure
from app.analysis.scanner import scan_repository
from app.errors import AnalysisError
from app.ingestion.archive import extract_repository
from app.ml.inference import UnavailableModel


def test_real_scanned_summary(make_zip, sample_files, tmp_path):
    ingestion = extract_repository(make_zip(sample_files), tmp_path)
    result = scan_repository(tmp_path, "example.zip", ingestion)
    assert asdict(result.summary) == {
        "files": 4, "source_files": 2, "directories": 4, "languages": 4,
        "bytes": sum(len(sample_files[name].encode()) for name in ["repo/src/main.py", "repo/src/app.js", "repo/README.md", "repo/config.json"]),
        "total_lines": 10, "source_lines": 6, "blank_lines": 2, "known_comment_lines": 1,
        "comment_counted_files": 2, "comment_uncounted_files": 2, "skipped_files": 4,
    }
    assert sum(language.files for language in result.languages) == 4
    assert all(language.percentage == 25.0 for language in result.languages)
    assert result.largest_files[0].path == "repo/src/app.js"
    assert result.schema_version == "1.0"


@pytest.mark.parametrize("text,language,lines,blank,comments,code", [
    ("# comment\n\nx=1 # inline\n", "Python", 3, 1, 1, 1),
    ('x = "# not a comment"\n', "Python", 1, 0, 0, 1),
    ('doc = """text\n# inside string\n"""\n# outside\n', "Python", 4, 0, 1, 3),
    ('# comment\nx = (', "Python", 2, 0, None, None),
    ("", "Python", 0, 0, 0, 0),
    ("\n\n", "Python", 2, 2, 0, 0),
    ("x=1\r\n# comment\r\n", "Python", 2, 0, 1, 1),
    ("# comment\rx=1\r", "Python", 2, 0, 1, 1),
    ("x=1", "Python", 1, 0, 0, 1),
    ('// comment\nlet x=1;\n', "JavaScript", 2, 0, None, None),
    ('{"x": 1}\n', "JSON", 1, 0, 0, 1),
    ('// not standard JSON\n{}', "JSON", 2, 0, None, None),
    ('# known\nx="unterminated\n', "Python", 2, 0, None, None),
])
def test_line_semantics(text, language, lines, blank, comments, code):
    assert measure(text, language) == {"lines": lines, "blank_lines": blank,
                                     "nonblank_lines": lines - blank, "comment_lines": comments,
                                     "code_lines": code}


def test_binary_and_non_utf8(make_zip, tmp_path):
    ingestion = extract_repository(make_zip({"bad.py": b"\x00binary", "old.txt": b"\xff\xfe", "ok.py": b"\xef\xbb\xbfx=1\n"}), tmp_path)
    result = scan_repository(tmp_path, "repo.zip", ingestion)
    assert [file.path for file in result.files] == ["ok.py"]
    assert result.skipped == {"binary_or_non_utf8": 2}


def test_no_supported_text(make_zip, tmp_path):
    ingestion = extract_repository(make_zip({"bad.py": b"\x00binary"}), tmp_path)
    with pytest.raises(AnalysisError) as error:
        scan_repository(tmp_path, "repo.zip", ingestion)
    assert error.value.status == 422


def test_scanner_does_not_follow_symlinks(tmp_path):
    (tmp_path / "link.py").symlink_to("/etc/passwd")
    (tmp_path / "linked-directory").symlink_to("/etc", target_is_directory=True)
    (tmp_path / "ok.py").write_text("x=1")
    result = scan_repository(tmp_path, "repo.zip", {"skipped": {}, "archive_entries": 3})
    assert [file.path for file in result.files] == ["ok.py"]


def test_empty_text_file_is_valid(make_zip, tmp_path):
    ingestion = extract_repository(make_zip({"__init__.py": ""}), tmp_path)
    result = scan_repository(tmp_path, "repo.zip", ingestion)
    assert result.summary.files == 1
    assert result.summary.total_lines == 0
    assert result.languages[0].percentage == 100


def test_future_model_never_fabricates_predictions():
    with pytest.raises(NotImplementedError, match="No trained"):
        UnavailableModel().predict(None)
