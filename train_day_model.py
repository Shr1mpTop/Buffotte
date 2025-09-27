"""
训练日线涨幅预测模型。

流程：
- 从 MySQL 表 `kline_data_day` 或者 CSV 读取数据，必须包含字段 timestamp (秒), open_price, close_price, high_price, low_price, volume
- 计算目标 daily_return = (close_price - open_price) / open_price
- 构造滞后特征（默认过去 1..n 天的 close_price pct change）
- 最近 N 天（默认 30）作为验证集，其他作为训练集
- 训练 RandomForestRegressor 并保存模型与特征列表

用法示例：
  python train_day_model.py --config ./config.json --val-days 30 --lags 5 --out-dir models
  或者使用 csv： python train_day_model.py --csv data/day_kline.csv --val-days 30

"""
import argparse
import os
import joblib
import json
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from typing import Tuple

try:
    import pymysql
except Exception:
    pymysql = None


def read_from_db(config_path: str) -> pd.DataFrame:
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    conn = pymysql.connect(**cfg)
    df = pd.read_sql('SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp', conn)
    conn.close()
    # timestamp assumed to be in seconds
    df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


def read_from_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns:
        df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
    else:
        raise ValueError('CSV must contain timestamp column (seconds)')
    return df


def prepare_features(df: pd.DataFrame, lags: int = 5) -> pd.DataFrame:
    df = df.sort_values('timestamp').reset_index(drop=True)
    # 计算 daily return
    df['daily_return'] = (df['close_price'] - df['open_price']) / df['open_price']

    # 使用过去 lags 天的 close pct change 和 volume
    for lag in range(1, lags + 1):
        df[f'close_lag_{lag}'] = df['close_price'].shift(lag)
        df[f'close_pct_lag_{lag}'] = df['close_price'].pct_change(periods=lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)

    df = df.dropna().reset_index(drop=True)
    return df


def split_train_val(df: pd.DataFrame, val_days: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # 假设 df 按时间排序
    last_ts = df['dt'].max()
    cutoff = last_ts - pd.Timedelta(days=val_days)
    train = df[df['dt'] < cutoff].copy()
    val = df[df['dt'] >= cutoff].copy()
    return train, val


def train_and_save(train: pd.DataFrame, val: pd.DataFrame, feature_cols: list, out_dir: str):
    X_train = train[feature_cols].values
    y_train = train['daily_return'].values
    X_val = val[feature_cols].values
    y_val = val['daily_return'].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_val_s)
    mse = mean_squared_error(y_val, y_pred)
    print(f"Validation MSE: {mse}")

    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, f'rf_day_model_{int(time.time())}.joblib')
    scaler_path = os.path.join(out_dir, f'scaler_day_{int(time.time())}.joblib')
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Saved model to {model_path}")
    print(f"Saved scaler to {scaler_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='db config json path')
    parser.add_argument('--csv', help='csv file path (timestamp in seconds)')
    parser.add_argument('--val-days', type=int, default=30)
    parser.add_argument('--lags', type=int, default=5)
    parser.add_argument('--out-dir', default='models')
    args = parser.parse_args()

    if not args.config and not args.csv:
        raise ValueError('Provide either --config (DB) or --csv')

    if args.config:
        if pymysql is None:
            raise RuntimeError('pymysql not installed')
        df = read_from_db(args.config)
    else:
        df = read_from_csv(args.csv)

    dfp = prepare_features(df, lags=args.lags)
    train, val = split_train_val(dfp, val_days=args.val_days)

    # 选择特征列
    feat_cols = []
    for lag in range(1, args.lags + 1):
        feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']

    print(f"Train samples: {len(train)}, Val samples: {len(val)}")

    train_and_save(train, val, feat_cols, args.out_dir)


if __name__ == '__main__':
    main()
