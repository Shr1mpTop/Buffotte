@echo off
REM Buffotte v0.6.1 Windows部署脚本

echo === Buffotte v0.6.1 模块化架构部署 ===

REM 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 安装Python依赖
echo 安装Python爬虫依赖...
cd crawler
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: Python依赖安装失败，某些功能可能不可用
)
cd ..

REM 检查Node.js环境
echo 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

REM 安装后端依赖
echo 安装后端依赖...
cd backend
npm install
if errorlevel 1 (
    echo 错误: 后端依赖安装失败
    pause
    exit /b 1
)
cd ..

REM 安装前端依赖
echo 安装前端依赖...
cd frontend
npm install
if errorlevel 1 (
    echo 错误: 前端依赖安装失败
    pause
    exit /b 1
)
cd ..

echo === 部署完成 ===
echo 版本: v0.6.1
echo 架构: 模块化
echo.
echo 启动命令:
echo 后端: cd backend ^&^& npm start
echo 前端: cd frontend ^&^& npm run dev  
echo 爬虫: cd crawler ^&^& python main.py batch --max-pages 100
pause