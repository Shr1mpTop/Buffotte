#!/bin/bash

# Buffotte 热点饰品自动化脚本
# 执行流水线：Scout(搜索新闻) → Parser(提取实体) → Investigator(爬取价格) → 新闻分类
# 建议 cron: 每天 8:00（在 daily_automation 之后 1 小时执行）
# 0 8 * * * /root/Buffotte/skin_automation.sh >> /root/Buffotte/logs/skin_automation.log 2>&1

set -e

cd /root/Buffotte

CONTAINER="buffotte-backend-1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=========================================="
echo "🔫 饰品流水线启动 @ $TIMESTAMP"
echo "=========================================="

# ─── Phase 1-3: Orchestrator 流水线 ──────────────────────────────
echo "▶ [Phase 1-3] 执行 Orchestrator 流水线 (Scout → Parser → Investigator)..."
docker exec "$CONTAINER" python -c "
import logging, sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s %(message)s')
from llm.orchestrator import run_pipeline
stats = run_pipeline(investigator_batch_size=15)
print()
print('=== 流水线统计 ===')
for phase in ['scout', 'parser', 'investigator']:
    print(f'  {phase}: {stats.get(phase, {})}')
print(f'  总耗时: {stats.get(\"elapsed_seconds\", 0):.1f}s')
"

if [ $? -ne 0 ]; then
    echo "❌ Orchestrator 流水线失败"
    exit 1
fi
echo "✅ Orchestrator 流水线完成"

# ─── Phase 4: 新闻分类 ──────────────────────────────────────────
echo ""
echo "▶ [Phase 4] 运行新闻分类器..."
docker exec "$CONTAINER" python -c "
import logging, sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s %(message)s')
from llm.agents.news_classifier import run_classifier
run_classifier()
"

if [ $? -ne 0 ]; then
    echo "⚠️  新闻分类器执行失败（不影响主流程）"
else
    echo "✅ 新闻分类完成"
fi

echo ""
echo "=========================================="
echo "🏁 饰品流水线结束 @ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
