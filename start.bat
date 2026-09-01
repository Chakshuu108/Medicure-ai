@echo off
echo Starting MediCure AI Platform...
echo.
echo 1. Make sure Docker Desktop is running
echo 2. PostgreSQL: docker compose up -d
echo 3. Backend:  cd backend ^&^& uvicorn app.main:app --reload --port 8000
echo 4. Frontend: cd frontend ^&^& npm run dev
echo.
echo Demo logins at http://localhost:5173
pause
