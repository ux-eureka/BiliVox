@echo off
setlocal
echo ============================================
echo  Starting BiliVox Local Server
echo ============================================
cd /d "%~dp0"

echo [1/2] Building latest frontend (Vite)...
pushd frontend
call npm run build
popd

echo [2/2] Starting backend (FastAPI) on port 8000...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info

echo.
echo Server stopped. Press any key to exit.
pause
endlocal
