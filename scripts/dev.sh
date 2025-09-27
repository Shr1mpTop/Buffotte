#!/bin/bash

# Buffotte 项目开发脚本

case "$1" in
  "install")
    echo "安装所有依赖..."
    cd backend && npm install
    cd ../frontend && npm install
    cd ../crawler && pip install -r requirements.txt
    ;;
  "start")
    echo "启动所有服务..."
    # 启动后端
    cd backend && npm start &
    # 启动前端
    cd ../frontend && npm run dev &
    # 等待服务启动
    sleep 3
    echo "服务已启动："
    echo "- 后端: http://localhost:3000"
    echo "- 前端: http://localhost:5173"
    ;;
  "stop")
    echo "停止所有服务..."
    pkill -f "node.*server.js"
    pkill -f "vite"
    ;;
  "crawl")
    echo "运行爬虫..."
    cd crawler && python src/kline_crawler.py
    ;;
  "db:init")
    echo "初始化数据库..."
    mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS buffotte;"
    ;;
  *)
    echo "使用方法: $0 {install|start|stop|crawl|db:init}"
    echo "  install  - 安装所有依赖"
    echo "  start    - 启动开发服务器"
    echo "  stop     - 停止所有服务"
    echo "  crawl    - 运行数据爬虫"
    echo "  db:init  - 初始化数据库"
    ;;
esac