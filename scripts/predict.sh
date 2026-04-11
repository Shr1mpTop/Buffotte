#!/bin/bash
cd /root/Buffotte

# 在backend容器内运行
docker exec buffotte-backend-1 python models/train_model.py
if [ $? -ne 0 ]; then
    echo "❌ 数据训练预测失败，退出脚本"
    exit 1
fi
