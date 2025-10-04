# LSTM超参数优化使用指南

## 概述

使用Optuna进行LSTM模型的自动超参数优化，支持贝叶斯优化和网格搜索两种模式。

## 安装依赖

```bash
pip install optuna plotly kaleido
```

或使用conda:

```bash
conda install -c conda-forge optuna plotly python-kaleido
```

## 快速开始

### 1. 贝叶斯优化（推荐）

贝叶斯优化使用智能采样策略，在较少试验次数下找到较优参数。

```bash
cd src
python lstm_hyperopt.py --mode bayesian --n-trials 50
```

**参数说明：**
- `--mode bayesian`: 使用贝叶斯优化
- `--n-trials 50`: 进行50次试验
- `--timeout 3600`: 可选，设置1小时超时限制（秒）
- `--train-best`: 可选，优化完成后用最佳参数训练完整模型

### 2. 网格搜索

网格搜索详尽地搜索所有参数组合，适用于参数空间较小的情况。

```bash
python lstm_hyperopt.py --mode grid
```

### 3. 使用最佳参数训练完整模型

```bash
python lstm_hyperopt.py --mode bayesian --n-trials 100 --train-best
```

## 优化的超参数

### 模型架构参数
- `seq_length`: 序列长度 (10-40, 步长5)
- `hidden_size`: 隐藏层大小 (32, 64, 128, 256)
- `num_layers`: LSTM层数 (1-4)
- `dropout`: Dropout比例 (0.0-0.5)

### 训练参数
- `batch_size`: 批次大小 (16, 32, 64, 128)
- `learning_rate`: 学习率 (1e-5 到 1e-2, 对数均匀分布)
- `optimizer`: 优化器类型 (Adam, AdamW, RMSprop)
- `scheduler_patience`: 学习率调度器耐心值 (3-10)
- `scheduler_factor`: 学习率衰减因子 (0.3-0.7)

## 输出结果

优化完成后，会在 `models/hyperopt/` 目录下生成：

### 1. 最佳配置文件
`best_config_YYYYMMDD_HHMMSS.json` - 可直接用于训练的配置

```json
{
  "seq_length": 25,
  "hidden_size": 128,
  "num_layers": 3,
  "dropout": 0.3,
  "batch_size": 32,
  "learning_rate": 0.0003,
  "optimizer": "AdamW",
  "scheduler_patience": 5,
  "scheduler_factor": 0.5,
  ...
}
```

### 2. 所有试验结果
`trials_YYYYMMDD_HHMMSS.csv` - 包含所有试验的参数和结果

### 3. Study对象
`study_YYYYMMDD_HHMMSS.pkl` - 可用于后续分析的完整优化对象

### 4. 可视化图表
- `optimization_history_*.png` - 优化历史趋势
- `param_importances_*.png` - 参数重要性排名
- `parallel_coordinate_*.png` - 参数平行坐标图
- `analysis_*.png` - 详细分析图表（4张子图）

## 使用最佳配置

### 方法1: 替换配置文件

```bash
# 复制最佳配置
cp models/hyperopt/best_config_*.json lstm_config.json

# 使用新配置训练
python lstm_trainer.py
```

### 方法2: Python API

```python
from lstm_trainer import LSTMTrainer

# 使用最佳配置
trainer = LSTMTrainer(
    config_path='config.json',
    lstm_config_path='models/hyperopt/best_config_20251004_150000.json'
)

# 训练模型
training_info = trainer.train(save_model=True)
```

## 高级用法

### 自定义搜索空间

修改 `lstm_hyperopt.py` 中的 `define_search_space` 方法：

```python
def define_search_space(self, trial: optuna.Trial) -> Dict:
    config = self.base_config.copy()
    
    # 自定义搜索范围
    config['seq_length'] = trial.suggest_int('seq_length', 20, 50, step=10)
    config['hidden_size'] = trial.suggest_categorical('hidden_size', [128, 256, 512])
    
    # 添加新参数
    config['weight_decay'] = trial.suggest_loguniform('weight_decay', 1e-6, 1e-3)
    
    return config
```

### 加载已有Study继续优化

```python
import joblib
import optuna

# 加载已保存的study
study = joblib.load('models/hyperopt/study_20251004_150000.pkl')

# 继续优化
optimizer = LSTMHyperparameterOptimizer(n_trials=50)
study.optimize(optimizer.objective, n_trials=50)
```

### 并行优化（多进程）

```python
import optuna

# 使用SQLite数据库存储study
storage = 'sqlite:///lstm_hyperopt.db'

study = optuna.create_study(
    study_name='lstm_parallel',
    storage=storage,
    direction='minimize',
    load_if_exists=True
)

# 在多个终端运行
optimizer = LSTMHyperparameterOptimizer()
study.optimize(optimizer.objective, n_trials=20)
```

## 优化策略建议

### 1. 快速探索（20-30次试验）
适用于快速了解参数空间：

```bash
python lstm_hyperopt.py --mode bayesian --n-trials 20
```

### 2. 标准优化（50-100次试验）
平衡速度和效果：

```bash
python lstm_hyperopt.py --mode bayesian --n-trials 50
```

### 3. 深度优化（100+次试验）
追求最佳性能：

```bash
python lstm_hyperopt.py --mode bayesian --n-trials 200 --timeout 7200
```

### 4. 两阶段优化
第一阶段快速筛选，第二阶段精细调整：

```bash
# 阶段1: 粗粒度搜索
python lstm_hyperopt.py --mode bayesian --n-trials 50

# 阶段2: 在最佳参数附近精细搜索（需修改搜索空间）
python lstm_hyperopt.py --mode bayesian --n-trials 30
```

## 性能优化技巧

### 1. 使用数据缓存
脚本已自动缓存数据，避免重复加载。对于seq_length固定的试验，速度会快很多。

### 2. 限制训练轮数
优化过程中每个试验最多训练50个epoch，使用早停机制快速评估。

### 3. 启用剪枝
使用MedianPruner自动停止表现不佳的试验：

```python
pruner=optuna.pruners.MedianPruner(
    n_startup_trials=5,    # 前5个试验不剪枝
    n_warmup_steps=10      # 每个试验前10步不剪枝
)
```

### 4. 使用GPU
如果有NVIDIA GPU，会自动使用CUDA加速。

## 结果分析

### 查看参数重要性
参数重要性图（`param_importances_*.png`）显示哪些参数对性能影响最大。

**典型发现：**
- `learning_rate` 和 `hidden_size` 通常最重要
- `batch_size` 和 `scheduler_patience` 影响较小

### 分析参数关系
平行坐标图显示最佳试验的参数组合特征。

### 监控优化进度
优化历史图显示验证损失随试验次数的变化趋势。

## 常见问题

### Q: 优化时间太长怎么办？
**A:** 
- 减少 `--n-trials` 数量
- 设置 `--timeout` 时间限制
- 在 `objective` 函数中减少 `max_epochs`

### Q: 如何选择贝叶斯优化还是网格搜索？
**A:**
- **贝叶斯优化**: 参数空间大，试验预算有限（推荐）
- **网格搜索**: 参数空间小，需要详尽搜索

### Q: 验证损失波动很大？
**A:**
- 增加训练数据量
- 调整 `early_stopping_patience`
- 检查数据质量

### Q: 最佳参数在边界上？
**A:** 说明搜索空间可能不够，需要扩大搜索范围：

```python
# 扩大hidden_size范围
config['hidden_size'] = trial.suggest_categorical('hidden_size', [64, 128, 256, 512, 1024])
```

## 示例工作流

```bash
# 1. 安装依赖
pip install optuna plotly kaleido

# 2. 运行优化（50次试验）
cd src
python lstm_hyperopt.py --mode bayesian --n-trials 50

# 3. 查看结果
ls ../models/hyperopt/

# 4. 使用最佳配置训练完整模型
cp ../models/hyperopt/best_config_*.json ../lstm_config.json
python lstm_trainer.py

# 5. 查看可视化结果
explorer ..\models\hyperopt
```

## 参考资料

- [Optuna官方文档](https://optuna.readthedocs.io/)
- [超参数优化最佳实践](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/index.html)
- [贝叶斯优化原理](https://distill.pub/2020/bayesian-optimization/)

## 许可证

MIT License
