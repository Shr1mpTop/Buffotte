#!/bin/bash

# Buffotte 自动化每日任务脚本
# 北京时间 7:00 执行：数据训练预测 -> 新闻获取 -> 数据处理

echo "=== Buffotte 自动化任务开始 ==="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"

# 设置工作目录
cd /root/Buffotte

# 激活 conda 环境（如果需要）
# source /root/miniconda3/bin/activate buffotte

echo "=== 步骤 1: 执行数据训练和预测 ==="
python models/train_model.py
if [ $? -ne 0 ]; then
    echo "❌ 数据训练预测失败，退出脚本"
    exit 1
fi
echo "✅ 数据训练预测完成"

echo "=== 步骤 2: 获取每日新闻 ==="
# 循环获取新闻，直到找到参考文献
while true; do
    cd llm
    python test.py
    if [ $? -ne 0 ]; then
        echo "❌ 新闻获取失败，重试"
        sleep 5  # 等待5秒后重试
        continue
    fi
    cd ..
    
    echo "=== 检查新闻数据处理 ==="
    output=$(python -m db.news_processor 2>&1)
    if echo "$output" | grep -q "未找到任何参考文献"; then
        echo "❌ 未找到参考文献，重试获取新闻"
        sleep 5  # 等待5秒后重试
        continue
    fi
    echo "✅ 新闻获取和处理完成"
    break
done

echo "=== 步骤 4: 生成总结数据 ==="
python -m db.summary_processor
if [ $? -ne 0 ]; then
    echo "❌ 总结数据生成失败，退出脚本"
    exit 1
fi
echo "✅ 总结数据生成完成"

echo "=== 所有任务执行完成 ==="
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"