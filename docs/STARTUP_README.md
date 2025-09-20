# Buffotte 启动指南

## 🚀 快速启动

### 方法1: 一键启动（最简单）
双击运行 `快速启动.bat` - 自动启动前后端服务

### 方法2: 菜单式启动（推荐）
双击运行 `start.bat` 选择需要的服务：
- **选项1**: 仅启动后端服务 (http://localhost:3001)
- **选项2**: 仅启动前端服务 (http://localhost:5173)  
- **选项3**: 同时启动前端和后端
- **选项4**: 检查环境状态

## 📋 启动文件说明

| 文件 | 功能 | 使用场景 |
|------|------|----------|
| `快速启动.bat` | 一键启动前后端 | 日常开发，快速启动 |
| `start.bat` | 菜单式启动器 | 选择性启动，环境检查 |

## 🔧 环境要求
1. 安装 Anaconda/Miniconda
2. 创建 buffotte 环境：`conda create -n buffotte python=3.11`
3. 安装依赖：`conda run -n buffotte pip install -r requirements.txt`

#### 启动后端
```bash
cd backend
conda run -n buffotte npm run dev
```

#### 启动前端
```bash
cd frontend  
conda run -n buffotte npm run dev
```

## 环境检查

运行 `start.bat` 并选择选项4可以检查：
- ✅ conda 是否安装
- ✅ buffotte 环境是否存在
- ✅ Node.js 是否在环境中可用
- ✅ 端口 3001 和 5173 是否可用

## 故障排除

### 端口被占用
如果端口被占用，可以：
1. 关闭占用端口的程序
2. 或等待其自动释放
3. 使用任务管理器结束相关进程

### 环境问题
如果遇到环境问题：
1. 确保已激活 buffotte 环境
2. 重新安装依赖：`pip install -r requirements.txt`
3. 检查 Python 版本：`python --version`

### 数据库连接问题
确保 MySQL 服务正在运行，并且配置正确。

## 服务地址

- **前端**: http://localhost:5173
- **后端**: http://localhost:3001
- **API 文档**: http://localhost:3001/api

## 日志和调试

- 后端日志会显示在终端中
- 前端开发服务器日志会显示编译信息
- 爬虫日志包含数据获取和更新信息