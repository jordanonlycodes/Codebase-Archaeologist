import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.errors import AnalysisError
from app.middleware import UploadBoundary
from app.routes import analysis, dashboard

app = FastAPI(title="Codebase Archaeologist", version="0.1.0",
              description="Safe ZIP ingestion and deterministic repository metrics. Optional trusted C-function defect-risk inference.")
app.add_middleware(UploadBoundary)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(dashboard.router)
app.include_router(analysis.router)


@app.exception_handler(AnalysisError)
async def analysis_error(request: Request, exc: AnalysisError):
    return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse({"error": {"code": "invalid_request", "message": str(exc.detail)}}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse({"error": {"code": "invalid_request", "message": "The request does not match the API format."}}, status_code=422)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Repository analysis failed")
    return JSONResponse({"error": {"code": "internal_error", "message": "Analysis could not finish. Please retry or check the server logs."}}, status_code=500)


@app.middleware("http")
async def response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if response.headers.get("content-type", "").startswith("text/html") or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    return response
