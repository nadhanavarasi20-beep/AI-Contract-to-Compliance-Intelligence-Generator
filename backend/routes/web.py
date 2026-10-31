from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from backend.config import settings

router = APIRouter(tags=["Web UI"])

templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/")
async def get_dashboard(request: Request):
    """Renders the Executive Legal & Compliance Intelligence Dashboard."""
    context = {
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "display_model": settings.DISPLAY_MODEL_NAME,
        "has_env_key": bool(settings.GEMINI_API_KEY)
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)
