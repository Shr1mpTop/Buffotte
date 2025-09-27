@echo off
REM Buffotte 项目开发脚本 (Windows)

if "%1"=="install" goto install
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="crawl" goto crawl
if "%1"=="db:init" goto dbinit

echo 使用方法: %0 {install|start|stop|crawl|db:init}
echo   install  - 安装所有依赖
echo   start    - 启动开发服务器
echo   stop     - 停止所有服务
echo   crawl    - 运行数据爬虫
echo   db:init  - 初始化数据库
goto end

:install
echo 安装所有依赖...
cd backend && npm install
cd ../frontend && npm install
cd ../crawler && pip install -r requirements.txt
goto end

:start
echo 启动所有服务...
REM 启动后端
start cmd /k "cd backend && npm start"
REM 启动前端
start cmd /k "cd frontend && npm run dev"
echo 服务启动中...
timeout /t 3 >nul
echo 服务已启动：
echo - 后端: http://localhost:3000
echo - 前端: http://localhost:5173
goto end

:stop
echo 停止所有服务...
taskkill /f /im node.exe >nul 2>&1
goto end

:crawl
echo 运行爬虫...
cd crawler && python src/kline_crawler.py
goto end

:dbinit
echo 初始化数据库...
mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS buffotte;"
goto end

:end