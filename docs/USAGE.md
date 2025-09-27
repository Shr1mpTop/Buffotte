# 使用手册（Usage）

此文档面向项目管理层与工程人员，说明如何运行、复现训练、评估与预测，并包含交付清单。

## 目标
利用历史 Kline 数据构建日级涨幅预测模型，并把预测转为可回测的交易策略以检验盈利能力。

## 运行环境
- Python 3.8+（建议 3.10）
- 建议在虚拟环境中运行：venv 或 conda

## 安装依赖
```powershell
pip install -r requirements.txt
```

## 准备数据
- 在 `config.json` 中配置 MySQL 连接信息，脚本将从 `kline_data_day` 表读取数据（timestamp 单位为秒）。

## 训练模型
Baseline（RandomForest）示例：
```powershell
python .\train_day_model.py --config .\config.json --val-days 30 --lags 5 --out-dir models
```

输出：模型文件与 scaler 保存在 `models/`，并在控制台打印验证 MSE。

## 评估模型
```powershell
python .\evaluate_model.py --model models\rf_day_model_*.joblib --scaler models\scaler_day_*.joblib --config .\config.json --val-days 30 --lags 5
```

输出：控制台 JSON 报告，并保存为 `models/<modelname>.eval.json`。

## 预测（示例）
运行 `predict.py` 或 `predict_day_example.py`（示例脚本），加载模型并对最新数据做预测。

## 建议的实验路线（交付给老板的最小可交付成果）
1. Walk-forward LightGBM baseline：训练并给出每 fold 的评估与最终聚合结果（JSON+CSV），以及模型文件与 metadata。
2. 基线比较与统计检验（directional accuracy 的 p-value）。
3. 简单回测（考虑手续费/滑点）结果（年化收益、夏普、回撤），并输出策略曲线图。

## 交付清单（提交给老板）
- 完整源码（本仓库）
- 训练模型 & metadata（models/ 或 artifact）
- 评估报告与图表
- 使用手册（本文件）
- 最终汇报 PPT（可选）

## 风险与注意事项
- 数据样本量有限（818 天），请使用 walk-forward 验证而非单次静态划分。
- 模型对手续费与滑点敏感，需在回测中严格考虑成本。
- 模型文件不建议直接提交至普通 Git（使用 Git LFS 或上传到 release）。
