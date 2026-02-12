@echo off
setlocal
echo ============================================
echo  Starting BiliVox Local Server
echo ============================================
cd /d "%~dp0"

echo [1/3] Starting backend (FastAPI) on port 8000...
start "BiliVox Backend" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info"

echo [2/3] Starting frontend dev server on port 10086...
pushd frontend
start "BiliVox Frontend" cmd /c "npm run dev"
popd

echo.
echo ============================================
echo  Servers started:
echo  - Backend API:  http://localhost:8000
echo  - Frontend:    http://localhost:10086
echo ============================================
echo.
echo Press any key to stop all servers and exit...
pause

echo Stopping all servers...
taskkill /FI "WindowTitle eq BiliVox*" /F >nul 2>&1

echo Done.
endlocal
