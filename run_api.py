#!/usr/bin/env python3
"""
启动Buffotte Report API服务器

运行方法:
    python run_api.py

服务器将在 http://localhost:8000 启动
API文档: http://localhost:8000/docs
"""

import uvicorn
from api import app

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )