# 部署指南

## Docker Compose 部署（推荐）

### 1. 环境准备

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh

# 克隆项目
git clone https://github.com/Shr1mpTop/Buffotte.git
cd Buffotte
```

### 2. 配置环境变量

```bash
cp .env.example .env
vim .env
```

填入实际配置：

```ini
# MySQL 数据库
HOST=your_mysql_host
PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DATABASE=buffotte
CHARSET=utf8mb4

# 豆包 LLM
ARK_API_KEY=your_ark_api_key
DOUBAO_MODEL=your_model_endpoint

# Buff-Tracker 代理
BUFFTRACKER_URL=http://host.docker.internal:8001
```

### 3. 构建并启动

```bash
docker compose up -d --build
```

服务端口映射：

| 服务 | 容器端口 | 宿主机端口 | 说明 |
|------|---------|-----------|------|
| backend | 8000 | 8002 | FastAPI API 服务 |
| frontend | 80 | 4000 | Nginx 静态文件 |

### 4. 验证部署

```bash
# 检查服务状态
docker compose ps

# 检查后端健康
curl http://localhost:8002/api/system/stats

# 查看日志
docker compose logs -f backend
```

## 自动化任务配置

### Cron 定时任务

```bash
# 编辑 crontab
crontab -e
```

添加以下定时任务：

```cron
# 每日 07:00 (UTC+8 = 23:00 UTC 前一天) 执行新闻+分析
0 7 * * * /root/Buffotte/scripts/daily_automation.sh >> /var/log/buffotte-daily.log 2>&1

# 每小时（除 07:00 外）更新 K 线数据
0 * * * * /root/Buffotte/scripts/hourly_automation.sh >> /var/log/buffotte-hourly.log 2>&1
```

### 手动执行

```bash
# 手动训练模型 + 生成预测
bash scripts/predict.sh

# 手动刷新 K 线数据
bash scripts/kline_daily_refresh.sh

# 手动运行 AI 流水线
python llm/orchestrator.py
```

## Nginx 反向代理（生产环境）

前端容器已包含 Nginx 配置。如需在生产环境使用 HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name buffotte.hezhili.online;

    ssl_certificate     /etc/letsencrypt/live/buffotte.hezhili.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/buffotte.hezhili.online/privkey.pem;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:4000;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 监控

- **系统状态 API**: `GET /api/system/stats` — CPU、内存、负载、运行时间
- **Docker 日志**: `docker compose logs -f`
- **PM2 日志**: `logs/` 目录下

## 常见问题

### 数据库连接失败

1. 检查 `.env` 配置是否正确
2. 确认 MySQL 允许远程连接
3. Docker 内部使用 `host.docker.internal` 访问宿主机服务

### 爬虫获取数据失败

1. 检查 Chromium 是否正常安装: `playwright install chromium`
2. 容器内内存不足（建议 ≥ 1GB）
3. SteamDT WAF 策略更新，需要调整反检测参数

### 前端无法访问 API

1. 检查 CORS 配置 (`api.py` 中的 `allow_origins`)
2. 确认后端服务正常运行
3. 检查 Nginx 代理配置
