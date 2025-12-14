import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import os
import sys
import subprocess
import pymysql
from dotenv import load_dotenv

# 定义评估函数：皮尔逊相关系数
def pearson_correlation(y_true, y_pred):
    """
    计算皮尔逊相关系数。
    """
    corr = np.corrcoef(y_true, y_pred)[0, 1]
    return corr

def get_db_connection():
    """
    建立并返回数据库连接。
    """
    load_dotenv()
    try:
        config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT')),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET')
        }
        return pymysql.connect(**config)
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def save_predictions_to_db(predictions_df):
    """
    将预测结果保存到数据库的新表中。
    """
    conn = get_db_connection()
    if not conn:
        print("!!! 无法连接到数据库，跳过保存预测结果。")
        return

    print("\n--- 开始将预测结果保存到数据库 ---")
    try:
        with conn.cursor() as cursor:
            # 1. 创建预测表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS kline_data_prediction (
                date DATE PRIMARY KEY,
                predicted_close_price DECIMAL(10, 2),
                rolling_mean_7 DECIMAL(10, 2),
                rolling_std_7 DECIMAL(10, 2),
                rolling_mean_14 DECIMAL(10, 2),
                rolling_std_14 DECIMAL(10, 2),
                rolling_mean_30 DECIMAL(10, 2),
                rolling_std_30 DECIMAL(10, 2)
            )
            """
            cursor.execute(create_table_sql)
            print("预测表 'kline_data_prediction' 已确认存在。")

            # 确保 date 唯一，避免重复行累积
            cursor.execute(
                """
                SELECT COUNT(1) FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = 'kline_data_prediction'
                  AND index_name = 'idx_date_unique'
                """
            )
            has_unique_index = cursor.fetchone()[0] > 0
            if not has_unique_index:
                cursor.execute("ALTER TABLE kline_data_prediction ADD UNIQUE KEY idx_date_unique (date)")
                print("已为 kline_data_prediction 添加唯一索引 idx_date_unique。")

            # 3. 插入或更新新的预测数据
            insert_sql = """
            INSERT INTO kline_data_prediction (
                date, predicted_close_price, rolling_mean_7, rolling_std_7,
                rolling_mean_14, rolling_std_14, rolling_mean_30, rolling_std_30
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                predicted_close_price = VALUES(predicted_close_price),
                rolling_mean_7 = VALUES(rolling_mean_7),
                rolling_std_7 = VALUES(rolling_std_7),
                rolling_mean_14 = VALUES(rolling_mean_14),
                rolling_std_14 = VALUES(rolling_std_14),
                rolling_mean_30 = VALUES(rolling_mean_30),
                rolling_std_30 = VALUES(rolling_std_30)
            """
            
            # 准备要插入的数据, 将 NaN 替换为 None 以便数据库存储为 NULL
            data_to_insert = [
                tuple(row) for row in predictions_df.where(pd.notna(predictions_df), None).to_numpy()
            ]

            cursor.executemany(insert_sql, data_to_insert)
            conn.commit()
            print(f"成功将 {len(data_to_insert)} 条预测数据插入或更新到数据库。")

    except Exception as e:
        print(f"!!! 保存预测数据到数据库时发生错误: {e}")
        conn.rollback()
    finally:
        if conn.open:
            conn.close()
            print("数据库连接已关闭。")

def run_script(module_path, cwd):
    """
    将指定的 Python 脚本作为模块执行。
    """
    try:
        print(f"--- 开始执行模块: {module_path} ---")
        # 使用 -m 将脚本作为模块运行，并设置工作目录为项目根目录
        result = subprocess.run(
            [sys.executable, "-m", module_path],
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        print(result.stdout)
        print(f"--- 模块 {module_path} 执行成功 ---")
    except subprocess.CalledProcessError as e:
        print(f"!!! 执行 {module_path} 时发生错误 !!!")
        print(e.stderr)
        raise

def train_and_predict():
    """
    完整的模型训练、评估和预测流程。
    """
    # --- 步骤 0: 更新数据 ---
    print("步骤 0: 更新数据...")

    # 获取项目根目录的绝对路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 定义需要执行的模块
    kline_processor_module = 'db.kline_data_processor'
    create_dataset_module = 'db.create_dataset'

    # 依次执行脚本
    run_script(kline_processor_module, project_root)
    run_script(create_dataset_module, project_root)
    
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
    # 时间戳默认为 UTC，我们将其转换为 UTC+8 (Asia/Shanghai)
    data['date'] = pd.to_datetime(data['timestamp'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')
    data.set_index('date', inplace=True)
    data.sort_index(inplace=True)

    # --- 步骤 2: 特征工程 (在除去最后一行的数据上进行) ---
    print("步骤 2: 特征工程...")

    # 分离出最后一行用于后续的迭代预测
    data_for_prediction = data.iloc[-1:].copy()
    data_for_training = data.iloc[:-1].copy()
    
    # 目标变量：未来1天的收盘价
    data_for_training['target'] = data_for_training['close_price'].shift(-1)

    # 时间特征
    data_for_training['day_of_week'] = data_for_training.index.dayofweek
    data_for_training['month'] = data_for_training.index.month
    data_for_training['year'] = data_for_training.index.year

    # 滞后特征
    for lag in [7, 14, 30]:
        data_for_training[f'close_lag_{lag}'] = data_for_training['close_price'].shift(lag)

    # 滑动窗口特征
    for window in [7, 14, 30]:
        data_for_training[f'close_rolling_mean_{window}'] = data_for_training['close_price'].rolling(window=window).mean()
        data_for_training[f'close_rolling_std_{window}'] = data_for_training['close_price'].rolling(window=window).std()
        data_for_training[f'volume_rolling_mean_{window}'] = data_for_training['volume'].rolling(window=window).mean()

    # 清理因特征工程产生的 NaN 值
    data_for_training.dropna(inplace=True)
    
    # --- 步骤 3: 划分数据集 ---
    print("步骤 3: 划分数据集...")
    
    features = [col for col in data_for_training.columns if col not in ['timestamp', 'target']]
    X = data_for_training[features]
    y = data_for_training['target']

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

    # 在预测前打印最后一个历史数据点的日期以进行调试
    last_historical_date = data.index[-1]
    print(f"DEBUG: 最后一个历史数据点的日期是: {last_historical_date}")

    # 'model' 已在训练集(前80%数据)上训练完成
    # 现在，我们使用验证集(最近20%的数据)对其进行微调，使其适应近期市场模式
    print(f"使用最近 {len(X_val)} 条数据进行模型微调...")
    model.fit(X_val, y_val,
              init_model=model,  # 从现有模型继续训练
              eval_set=[(X_val, y_val)], # 使用微-调数据自身进行监控
              callbacks=[lgb.early_stopping(10, verbose=False)]) # 为微调设置一个较短的早停
    
    print("模型微调完成。")

    # --- 为预测准备初始特征 ---
    # 我们需要为 data_for_prediction 计算与训练时相同的特征
    
    # 完整的数据历史（包括用于训练的数据和用于预测的最后一行）
    full_history_df = pd.concat([data_for_training, data_for_prediction])
    
    # 时间特征
    data_for_prediction['day_of_week'] = data_for_prediction.index.dayofweek
    data_for_prediction['month'] = data_for_prediction.index.month
    data_for_prediction['year'] = data_for_prediction.index.year

    # 滞后特征
    for lag in [7, 14, 30]:
        data_for_prediction[f'close_lag_{lag}'] = full_history_df['close_price'].shift(lag).iloc[-1]

    # 滑动窗口特征
    for window in [7, 14, 30]:
        data_for_prediction[f'close_rolling_mean_{window}'] = full_history_df['close_price'].rolling(window=window).mean().iloc[-1]
        data_for_prediction[f'close_rolling_std_{window}'] = full_history_df['close_price'].rolling(window=window).std().iloc[-1]
        data_for_prediction[f'volume_rolling_mean_{window}'] = full_history_df['volume'].rolling(window=window).mean().iloc[-1]
    
    last_data_point_features = data_for_prediction[features].copy()
    last_known_date = data_for_prediction.index[0]
    
    future_steps = 30
    future_records = []

    # 将所有已知收盘价（包括最后一行）转换为列表
    close_price_history = full_history_df['close_price'].tolist()
    
    for i in range(future_steps):
        # 准备当前时间点的特征
        current_features = last_data_point_features
        
        # 使用微调后的模型进行预测
        next_day_pred = model.predict(current_features)[0]

        # 更新历史价格列表以包含新的预测值
        close_price_history.append(next_day_pred)
        
        # 计算下一个日期
        next_date = last_known_date + pd.Timedelta(days=i + 1)
        
        # --- 为下一次迭代准备新的特征 ---
        next_features = current_features.copy()
        next_features.index = [next_date] # 更新索引为新日期
        
        # 更新时间特征
        next_features['day_of_week'] = next_date.dayofweek
        next_features['month'] = next_date.month
        next_features['year'] = next_date.year

        # 使用扩展后的历史价格来计算滞后和滚动特征
        temp_series = pd.Series(close_price_history)

        for lag in [7, 14, 30]:
            if len(temp_series) > lag:
                next_features[f'close_lag_{lag}'] = temp_series.shift(lag).iloc[-1]
            else:
                next_features[f'close_lag_{lag}'] = np.nan
        
        for window in [7, 14, 30]:
            if len(temp_series) >= window:
                next_features[f'close_rolling_mean_{window}'] = temp_series.rolling(window=window).mean().iloc[-1]
                next_features[f'close_rolling_std_{window}'] = temp_series.rolling(window=window).std().iloc[-1]
            else:
                next_features[f'close_rolling_mean_{window}'] = np.nan
                next_features[f'close_rolling_std_{window}'] = np.nan

        # 记录当前步骤的详细预测信息
        record = {
            'day': next_date.strftime('%Y-%m-%d'),
            'predicted_close_price': next_day_pred,
            'rolling_mean_7': next_features[f'close_rolling_mean_7'].iloc[0] if f'close_rolling_mean_7' in next_features and not np.isnan(next_features[f'close_rolling_mean_7'].iloc[0]) else None,
            'rolling_std_7': next_features[f'close_rolling_std_7'].iloc[0] if f'close_rolling_std_7' in next_features and not np.isnan(next_features[f'close_rolling_std_7'].iloc[0]) else None,
            'rolling_mean_14': next_features[f'close_rolling_mean_14'].iloc[0] if f'close_rolling_mean_14' in next_features and not np.isnan(next_features[f'close_rolling_mean_14'].iloc[0]) else None,
            'rolling_std_14': next_features[f'close_rolling_std_14'].iloc[0] if f'close_rolling_std_14' in next_features and not np.isnan(next_features[f'close_rolling_std_14'].iloc[0]) else None,
            'rolling_mean_30': next_features[f'close_rolling_mean_30'].iloc[0] if f'close_rolling_mean_30' in next_features and not np.isnan(next_features[f'close_rolling_mean_30'].iloc[0]) else None,
            'rolling_std_30': next_features[f'close_rolling_std_30'].iloc[0] if f'close_rolling_std_30' in next_features and not np.isnan(next_features[f'close_rolling_std_30'].iloc[0]) else None
        }
        future_records.append(record)

        # 更新 last_data_point_features 以用于下一次迭代
        last_data_point_features = next_features

    # 保存预测结果
    predictions_df = pd.DataFrame(future_records)
    
    prediction_path = os.path.join(current_dir, 'next_month_prediction.csv')
    predictions_df.to_csv(prediction_path, index=False)
    print(f"未来 30 天的详细预测结果已保存到: {prediction_path}")

    # 新增步骤：将预测保存到数据库
    save_predictions_to_db(predictions_df)


if __name__ == "__main__":
    train_and_predict()
