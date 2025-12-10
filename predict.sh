cd /root/Buffotte

# 激活 conda 环境（如果需要）
# source /root/miniconda3/bin/activate buffotte

/root/miniconda3/bin/python models/train_model.py
if [ $? -ne 0 ]; then
    echo "❌ 数据训练预测失败，退出脚本"
    exit 1
fi
