from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import LIMITS

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


@router.get("/", include_in_schema=False)
async def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html")


@router.get("/explore", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html",
                                      context={"upload_limit": LIMITS.upload_bytes})


@router.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "codebase-archaeologist"}
