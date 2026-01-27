@echo off

rem BiliVox 启动脚本

cd /d %~dp0

echo ================================
echo BiliVox 视频资料库构建工具

echo ================================
echo 1. 安装前端依赖...
echo ================================
cd frontend
npm install
if %errorlevel% neq 0 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)

cd ..
echo ================================
echo 2. 安装后端依赖...
echo ================================
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 后端依赖安装失败！
    pause
    exit /b 1
)

cd ..
echo ================================
echo 3. 启动后端服务器...
echo ================================
start "BiliVox Backend" cmd /k "cd backend && python main.py"

rem 等待后端服务器启动
echo 等待后端服务器启动...
timeout /t 5 /nobreak >nul

echo ================================
echo 4. 启动前端服务器...
echo ================================
start "BiliVox Frontend" cmd /k "cd frontend && npm run dev"

echo ================================
echo 启动完成！
echo ================================
echo 前端地址: http://localhost:3000
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs

echo 按任意键关闭此窗口...
pause >nul
