#!/bin/bash
# Buffotte v0.6.1 部署脚本

echo "=== Buffotte v0.6.1 模块化架构部署 ==="

# 检查Python环境
echo "检查Python环境..."
python --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python，请先安装Python"
    exit 1
fi

# 安装Python依赖
echo "安装Python爬虫依赖..."
cd crawler
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "警告: Python依赖安装失败，某些功能可能不可用"
fi
cd ..

# 检查Node.js环境
echo "检查Node.js环境..."
node --version
npm --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 安装后端依赖
echo "安装后端依赖..."
cd backend
npm install
if [ $? -ne 0 ]; then
    echo "错误: 后端依赖安装失败"
    exit 1
fi
cd ..

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "错误: 前端依赖安装失败"
    exit 1
fi
cd ..

echo "=== 部署完成 ==="
echo "版本: v0.6.1"
echo "架构: 模块化"
echo ""
echo "启动命令:"
echo "后端: cd backend && npm start"
echo "前端: cd frontend && npm run dev"
echo "爬虫: cd crawler && python main.py batch --max-pages 100"