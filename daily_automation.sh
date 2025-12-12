#!/bin/bash

# Buffotte 自动化每日任务脚本
# 北京时间 7:00 执行: 新闻获取 -> 数据处理

# 设置工作目录
cd /root/Buffotte
# 循环获取新闻，直到找到参考文献
while true; do
    docker exec buffotte-backend-1 sh -c "cd llm && python test.py"
    if [ $? -ne 0 ]; then
        echo "❌ 新闻获取失败，重试"
        sleep 5  # 等待5秒后重试
        continue
    fi
    
    output=$(docker exec buffotte-backend-1 python -m db.news_processor 2>&1)
    if echo "$output" | grep -q "未找到任何参考文献"; then
        echo "❌ 未找到参考文献，重试获取新闻"
        sleep 5  # 等待5秒后重试
        continue
    fi
    break
done

docker exec buffotte-backend-1 python -m db.summary_processor
if [ $? -ne 0 ]; then
    echo "❌ 总结数据生成失败，退出脚本"
    exit 1
fi