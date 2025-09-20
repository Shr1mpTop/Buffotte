@echo off
chcp 65001 >nul

echo 🚀 Buffotte 快速启动...

cd /d "%~dp0"

echo 📦 启动后端服务...
start "Buffotte-后端" /d "%~dp0backend" cmd /c "conda run -n buffotte npm run dev & pause"

timeout /t 3 /nobreak >nul

echo 📦 启动前端服务...  
start "Buffotte-前端" /d "%~dp0frontend" cmd /c "conda run -n buffotte npm run dev & pause"

echo ✅ 启动完成！
echo 🌐 前端: http://localhost:5173
echo 🌐 后端: http://localhost:3001

timeout /t 3 >nul