# 快速开始

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐使用 conda 或 venv |
| Node.js | 20+ | 前端构建 |
| MySQL | 5.7+ | 数据存储 |
| Docker | 24+ | 容器化部署（可选） |

## 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/Shr1mpTop/Buffotte.git
cd Buffotte
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下配置：

```ini
# 数据库
HOST=your_mysql_host
PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DATABASE=buffotte
CHARSET=utf8mb4

# LLM（豆包）
ARK_API_KEY=your_ark_api_key
DOUBAO_MODEL=your_model_endpoint

# 外部服务
BUFFTRACKER_URL=http://localhost:8001
```

### 3. 后端启动

```bash
# 安装依赖
pip install -e .

# 启动开发服务器（热重载）
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

后端启动后：
- API 地址: `http://localhost:8000`
- Swagger 文档: `http://localhost:8000/docs`
- 在线文档: `http://localhost:8000/wiki`

### 4. 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器: `http://localhost:5173`

## Docker 部署

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看日志
docker compose logs -f
```

| 服务 | 端口映射 | 说明 |
|------|---------|------|
| backend | 8002 → 8000 | FastAPI 后端 |
| frontend | 4000 → 80 | Nginx 静态服务 |

## 常用命令

```bash
# 训练价格预测模型
python models/train_model.py

# 手动抓取大盘K线数据
python -m db.kline_data_processor

# 手动运行新闻分析流水线
python llm/orchestrator.py

# 查看系统状态
curl http://localhost:8000/api/system/stats
```
