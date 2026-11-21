from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from app.analysis.models import AnalysisResult
from app.analysis.scanner import scan_repository
from app.config import LIMITS
from app.ml.repository import analyze_functions
from app.errors import AnalysisError
from app.ingestion.archive import extract_repository

router = APIRouter(prefix="/api", tags=["analysis"])


def analyze_upload(upload: UploadFile) -> AnalysisResult:
    filename = (upload.filename or "repository.zip").replace("\\", "/").rsplit("/", 1)[-1]
    if len(filename.encode("utf-8")) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in filename):
        raise AnalysisError("Use a ZIP filename under 256 bytes without control characters.", "invalid_filename")
    if not filename.lower().endswith(".zip"):
        raise AnalysisError("Choose a .zip repository archive.", "unsupported_file", 415)
    if upload.size is not None and upload.size > LIMITS.upload_bytes:
        raise AnalysisError("ZIP exceeds the 25 MiB upload limit.", "upload_limit", 413)
    with TemporaryDirectory(prefix="archaeologist-") as temporary:
        root = Path(temporary)
        ingestion = extract_repository(upload.file, root)
        result = scan_repository(root, filename, ingestion)
        result.defect_risk = analyze_functions(root, result.files)
        return result


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
