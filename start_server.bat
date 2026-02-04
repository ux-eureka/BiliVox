@echo off
echo Starting BiliVox Server...
cd /d "%~dp0"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 10086 --log-level info
pause