import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import os

# 定义评估函数：皮尔逊相关系数
def pearson_correlation(y_true, y_pred):
    """
    计算皮尔逊相关系数。
    """
    corr = np.corrcoef(y_true, y_pred)[0, 1]
    return corr

def train_and_predict():
    """
    完整的模型训练、评估和预测流程。
    """
    # --- 步骤 1: 加载与清洗数据 ---
    print("步骤 1: 加载与清洗数据...")
    
    # 构建训练集文件的路径
    try:
        current_dir = os.path.dirname(__file__)
        csv_path = os.path.join(current_dir, 'train.csv')
        data = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"错误: 'train.csv' 文件未在 '{current_dir}' 目录下找到。")
        return

    # 筛选掉价格或交易量为 0 的无效数据
    columns_to_check = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
    initial_rows = len(data)
    data = data[(data[columns_to_check] > 0).all(axis=1)]
    print(f"数据清洗完成：移除了 {initial_rows - len(data)} 行包含 0 值的数据。")

    # 将 timestamp 转换为日期时间格式，并设为索引
    data['date'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('date', inplace=True)
    data.sort_index(inplace=True)

    # --- 步骤 2: 特征工程 ---
    print("步骤 2: 特征工程...")
    
    # 目标变量：未来1天的收盘价
    data['target'] = data['close_price'].shift(-1)

    # 时间特征
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month
    data['year'] = data.index.year

    # 滞后特征
    for lag in [7, 14, 30]:
        data[f'close_lag_{lag}'] = data['close_price'].shift(lag)

    # 滑动窗口特征
    for window in [7, 14, 30]:
        data[f'close_rolling_mean_{window}'] = data['close_price'].rolling(window=window).mean()
        data[f'close_rolling_std_{window}'] = data['close_price'].rolling(window=window).std()
        data[f'volume_rolling_mean_{window}'] = data['volume'].rolling(window=window).mean()

    # 清理因特征工程产生的 NaN 值
    data.dropna(inplace=True)
    
    # --- 步骤 3: 划分数据集 ---
    print("步骤 3: 划分数据集...")
    
    features = [col for col in data.columns if col not in ['timestamp', 'target']]
    X = data[features]
    y = data['target']

    # 按时间顺序划分，后 20% 为验证集
    train_size = int(len(X) * 0.8)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]

    print(f"训练集大小: {len(X_train)} | 验证集大小: {len(X_val)}")

    # --- 步骤 4: 模型训练与评估 ---
    print("步骤 4: 模型训练与评估...")
    
    lgb_params = {
        'objective': 'regression_l1',
        'metric': 'rmse',
        'n_estimators': 1000,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42
    }

    model = lgb.LGBMRegressor(**lgb_params)
    model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              eval_metric='rmse',
              callbacks=[lgb.early_stopping(100, verbose=False)])

    # 在验证集上评估
    y_pred_val = model.predict(X_val)
    score = pearson_correlation(y_val, y_pred_val)
    print(f"验证集上的皮尔逊相关系数 (ρ): {score:.4f}")

    # --- 步骤 5: 模型微调与未来预测 ---
    print("步骤 5: 模型微调与未来预测...")

    # 'model' 已在训练集(前80%数据)上训练完成
    # 现在，我们使用验证集(最近20%的数据)对其进行微调，使其适应近期市场模式
    print(f"使用最近 {len(X_val)} 条数据进行模型微调...")
    model.fit(X_val, y_val,
              init_model=model,  # 从现有模型继续训练
              eval_set=[(X_val, y_val)], # 使用微-调数据自身进行监控
              callbacks=[lgb.early_stopping(10, verbose=False)]) # 为微调设置一个较短的早停
    
    print("模型微调完成。")

    # 准备进行迭代预测
    future_steps = 30
    last_data_point = data.iloc[-1:].copy()
    future_predictions = []

    for _ in range(future_steps):
        # 准备当前时间点的特征
        current_features = last_data_point[features]
        
        # 使用微调后的模型进行预测
        next_day_pred = model.predict(current_features)[0]
        future_predictions.append(next_day_pred)

        # 更新 last_data_point 以准备下一次迭代
        last_date = last_data_point.index[0]
        next_date = last_date + pd.Timedelta(days=1)
        
        # 创建新的数据行
        new_row = last_data_point.copy()
        new_row.index = [next_date]
        new_row['close_price'] = next_day_pred # 使用预测值更新收盘价
        
        # 更新其他依赖于 close_price 的特征（简化版，仅更新滞后和滚动特征）
        # 实际应用中可能需要更复杂的特征更新逻辑
        temp_history = pd.concat([data['close_price'], pd.Series(future_predictions, index=pd.to_datetime(last_date) + pd.to_timedelta(np.arange(1, len(future_predictions) + 1), unit='D'))])

        new_row['day_of_week'] = next_date.dayofweek
        new_row['month'] = next_date.month
        new_row['year'] = next_date.year

        for lag in [7, 14, 30]:
            new_row[f'close_lag_{lag}'] = temp_history.shift(lag).iloc[-1]
        
        for window in [7, 14, 30]:
            new_row[f'close_rolling_mean_{window}'] = temp_history.rolling(window=window).mean().iloc[-1]
            new_row[f'close_rolling_std_{window}'] = temp_history.rolling(window=window).std().iloc[-1]
        
        last_data_point = new_row


    # 保存预测结果
    future_day_indices = range(1, future_steps + 1)
    predictions_df = pd.DataFrame({
        'day': future_day_indices,
        'predicted_close_price': future_predictions
    })
    
    prediction_path = os.path.join(current_dir, 'next_month_prediction.csv')
    predictions_df.to_csv(prediction_path, index=False)
    print(f"未来 30 天的预测结果已保存到: {prediction_path}")

if __name__ == "__main__":
    train_and_predict()
