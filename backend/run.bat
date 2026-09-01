@echo off
cd /d "%~dp0"
echo Starting MediCure API on http://localhost:8000
python -m uvicorn app.main:app --reload --port 8000
