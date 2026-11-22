from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile

from pydantic import BaseModel, ConfigDict, Field

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from app.analysis.models import AnalysisResult, RepositorySource
from app.analysis.scanner import scan_repository
from app.config import LIMITS
from app.ml.repository import analyze_functions
from app.errors import AnalysisError
from app.ingestion.archive import extract_repository
from app.ingestion.github import parse_github_url, download_repository

router = APIRouter(prefix="/api", tags=["analysis"])


def analyze_upload(upload: UploadFile) -> AnalysisResult:
    filename = (upload.filename or "repository.zip").replace("\\", "/").rsplit("/", 1)[-1]
    if len(filename.encode("utf-8")) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in filename):
        raise AnalysisError("Use a ZIP filename under 256 bytes without control characters.", "invalid_filename")
    if not filename.lower().endswith(".zip"):
        raise AnalysisError("Choose a .zip repository archive.", "unsupported_file", 415)
    if upload.size is not None and upload.size > LIMITS.upload_bytes:
        raise AnalysisError("ZIP exceeds the 25 MiB upload limit.", "upload_limit", 413)
    return analyze_archive(upload.file, filename, RepositorySource('zip', filename=filename))


def analyze_archive(stream, repository: str, source: RepositorySource) -> AnalysisResult:
    """One extraction/scanning/inference path for both ingestion methods."""
    with TemporaryDirectory(prefix="archaeologist-") as temporary:
        root = Path(temporary)
        ingestion = extract_repository(stream, root)
        result = scan_repository(root, repository, ingestion)
        result.defect_risk = analyze_functions(root, result.files)
        result.source = source
        return result


class GitHubRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    url: str = Field(min_length=1, max_length=2048)


@router.post('/analyze/github', response_model=AnalysisResult)
async def analyze_github(payload: GitHubRequest):
    repo = parse_github_url(payload.url)
    with TemporaryFile(mode='w+b', prefix='archaeologist-github-') as archive:
        source = await download_repository(repo, archive)
        return await run_in_threadpool(analyze_archive, archive, f'{source.owner}/{source.name}', source)


@router.post("/analyze", response_model=AnalysisResult, openapi_extra={
    "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "required": ["file"], "properties": {"file": {"type": "string", "format": "binary"}}
    }}}}
})
async def analyze(request: Request):
    if not request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
        raise AnalysisError("Send one ZIP file as multipart/form-data using the 'file' field.", "invalid_request", 415)
    async with request.form(max_files=1, max_fields=0, max_part_size=1024) as form:
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise AnalysisError("Attach one ZIP file using the 'file' field.", "missing_file", 422)
        return await run_in_threadpool(analyze_upload, upload)
