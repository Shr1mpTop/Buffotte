#!/bin/bash
# Buffotte 每小时自动化任务脚本
# 每小时执行一次（除了7点）：更新日K实时数据

# 获取当前小时
current_hour=$(date +%H)

# 如果是7点，退出以避免与每日任务冲突
if [ "$current_hour" -eq 7 ]; then
    exit 0
fi

# 设置工作目录
cd /root/Buffotte

# 加载 .env 中的数据库参数
set -a
source /root/Buffotte/.env
set +a

# 在backend容器内运行，传入数据库参数
docker exec \
    -e HOST="$HOST" \
    -e PORT="$PORT" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD="$DB_PASSWORD" \
    -e DATABASE="$DATABASE" \
    -e CHARSET="$CHARSET" \
    buffotte-backend-1 python -m db.kline_data_processor
if [ $? -ne 0 ]; then
    echo "❌ 日K实时数据更新失败"
    exit 1
fi