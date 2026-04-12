#!/bin/bash
# Buffotte 每日K线数据刷新脚本
# 北京时间 8:30 执行: 刷新所有追踪饰品的K线缓存数据
# Cron: 30 8 * * * /root/Buffotte/kline_daily_refresh.sh >> /root/Buffotte/logs/kline_daily_refresh.log 2>&1

set -e

cd /root/Buffotte

# 加载 .env 中的数据库参数
set -a
source /root/Buffotte/.env
set +a

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "=========================================="
echo "K线缓存每日刷新启动 @ $TIMESTAMP"
echo "=========================================="

# ─── Step 1: 同步 CS2 饰品基础信息（每日一次，新增入库）─────────────────
echo "▶ [Step 1] 同步 CS2 饰品基础信息..."
docker exec \
    -e HOST="$HOST" \
    -e PORT="$PORT" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD="$DB_PASSWORD" \
    -e DATABASE="$DATABASE" \
    -e CHARSET="$CHARSET" \
    -e BUFFTRACKER_URL="$BUFFTRACKER_URL" \
    buffotte-backend-1 python -m db.cs2_items_processor

if [ $? -ne 0 ]; then
    echo "⚠️  饰品基础信息同步失败（不影响 K 线刷新，继续执行）"
else
    echo "✅ 饰品基础信息同步完成"
fi

echo ""

# ─── Step 2: 刷新所有追踪饰品的 K 线缓存 ──────────────────────────────
echo "▶ [Step 2] 刷新追踪饰品 K 线缓存..."
docker exec \
    -e HOST="$HOST" \
    -e PORT="$PORT" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD="$DB_PASSWORD" \
    -e DATABASE="$DATABASE" \
    -e CHARSET="$CHARSET" \
    buffotte-backend-1 python -m db.item_kline_processor --refresh-tracked

if [ $? -ne 0 ]; then
    echo "❌ K线缓存刷新失败"
    exit 1
fi

echo "✅ K线缓存刷新完成"
echo ""
echo "全部任务完成 @ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
