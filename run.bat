@echo off
TITLE AI Contract-to-Compliance Intelligence Generator
color 0B

echo ===============================================================================
echo       AI Contract-to-Compliance Intelligence Generator - Gemini-3.8-Flash
echo                  Legal ^& Compliance GenAI Review Pipeline
echo ===============================================================================

cd /d "%~dp0"

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Setting up .venv...
    py -3.11 -m venv .venv || python -m venv .venv
    echo [INFO] Installing required dependencies...
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [OK] Starting FastAPI Server...
echo [OK] Open your browser at: http://127.0.0.1:8050
echo ===============================================================================

start http://127.0.0.1:8050
.\.venv\Scripts\python.exe main.py

pause
