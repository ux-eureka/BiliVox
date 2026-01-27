@echo off
rem BiliVox 产品模式启动脚本（单进程提供前端+后端）

cd /d %~dp0

echo ================================
echo BiliVox 产品模式（固定入口）
echo ================================

echo 1. 安装前端依赖...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)

echo 2. 构建前端产物...
npm run build
if %errorlevel% neq 0 (
    echo 前端构建失败！
    pause
    exit /b 1
)
cd ..

echo 3. 安装后端依赖...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 后端依赖安装失败！
    pause
    exit /b 1
)

echo 4. 启动后端（同时托管前端）...
echo ================================
echo 打开: http://localhost:8000/
echo API:  http://localhost:8000/api
echo 文档: http://localhost:8000/docs
echo ================================
python main.py
