import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.config import settings
from backend.routes.api import router as api_router
from backend.routes.web import router as web_router

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Legal & Compliance GenAI System - Converts contracts and internal policies into validated, structured compliance intelligence using Gemini and RAG."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routers
app.include_router(web_router)
app.include_router(api_router)

if __name__ == "__main__":
    print("=" * 75)
    print(f" {settings.PROJECT_NAME}")
    print(f" Technology: Generative AI | Model: {settings.DISPLAY_MODEL_NAME}")
    print("=" * 75)
    print(f" [OK] Server running at: http://{settings.HOST}:{settings.PORT}")
    print(f" [OK] API Documentation at: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 75)
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
