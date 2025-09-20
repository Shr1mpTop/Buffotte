@echo off
chcp 65001 >nul
setlocal

echo.
echo ==========================================
echo       Buffotte 项目启动器 v1.0
echo ==========================================
echo.

cd /d "%~dp0"

REM 检查是否在正确目录
if not exist "backend\package.json" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

:menu
echo 📋 请选择操作:
echo.
echo   [1] 启动后端服务 (3001端口)
echo   [2] 启动前端服务 (5173端口)  
echo   [3] 同时启动前后端 (推荐)
echo   [4] 检查环境状态
echo   [0] 退出
echo.

set /p "choice=请输入选项 (0-4): "

if "%choice%"=="0" exit /b 0
if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend  
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto check_env

echo.
echo ❌ 无效选择，请重新输入
echo.
goto menu

:check_env
echo.
echo 🔍 正在检查环境...
echo.

REM 检查conda
conda --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Conda 未找到
    echo 💡 请安装 Anaconda 或 Miniconda
) else (
    echo ✅ Conda 已安装
)

REM 检查buffotte环境
conda env list 2>nul | findstr "buffotte" >nul
if errorlevel 1 (
    echo ❌ buffotte 环境不存在
    echo 💡 请运行: conda create -n buffotte python=3.11
) else (
    echo ✅ buffotte 环境已存在
)

REM 检查端口
netstat -ano 2>nul | findstr ":3001" >nul
if not errorlevel 1 (
    echo ⚠️  端口3001已占用 (后端)
) else (
    echo ✅ 端口3001可用 (后端)
)

netstat -ano 2>nul | findstr ":5173" >nul  
if not errorlevel 1 (
    echo ⚠️  端口5173已占用 (前端)
) else (
    echo ✅ 端口5173可用 (前端)
)

echo.
echo 检查完成！
pause
goto menu

:start_backend
echo.
echo 🚀 启动后端服务...
echo 📍 使用 buffotte 环境
echo 🌐 服务地址: http://localhost:3001
echo.

cd backend
conda run -n buffotte npm run dev
pause
goto menu

:start_frontend
echo.
echo 🚀 启动前端服务... 
echo 📍 使用 buffotte 环境
echo 🌐 服务地址: http://localhost:5173
echo.

cd frontend
conda run -n buffotte npm run dev
pause 
goto menu

:start_both
echo.
echo 🚀 同时启动前后端服务...
echo 📍 使用 buffotte 环境
echo 🌐 后端: http://localhost:3001
echo 🌐 前端: http://localhost:5173
echo.
echo 💡 将在新窗口中启动服务...
echo.

REM 启动后端
echo 📦 启动后端服务...
start "Buffotte-后端" /d "%~dp0backend" cmd /c "conda run -n buffotte npm run dev & pause"

REM 等待3秒
echo ⏳ 等待3秒后启动前端...
timeout /t 3 /nobreak >nul

REM 启动前端  
echo 📦 启动前端服务...
start "Buffotte-前端" /d "%~dp0frontend" cmd /c "conda run -n buffotte npm run dev & pause"

echo.
echo ✅ 启动完成！
echo.
echo 📖 服务启动可能需要几秒钟，请稍等...
echo 🌐 启动完成后可访问: http://localhost:5173
echo 💡 关闭窗口不会停止服务，请在对应窗口按Ctrl+C停止
echo.

pause
goto menu