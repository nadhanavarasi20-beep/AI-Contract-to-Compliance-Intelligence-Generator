import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "AI Contract-to-Compliance Intelligence Generator"
    PROJECT_VERSION: str = "1.0.0"
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    FALLBACK_MODEL: str = "gemini-1.5-flash"
    DISPLAY_MODEL_NAME: str = "Gemini-3.8-Flash"
    
    # API Rate Limiter to completely avoid 429 quota exhaustion
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
    REQUEST_DELAY_SECONDS: float = float(os.getenv("REQUEST_DELAY_SECONDS", "2.0"))
    
    # Storage Directories
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    SAMPLE_DIR: Path = BASE_DIR / "sample_data"
    
    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8050"))

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
