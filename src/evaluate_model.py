"""
Evaluate saved model on validation data.

Usage:
  python evaluate_model.py --model models/rf_day_model_*.joblib --scaler models/scaler_day_*.joblib --config config.json --val-days 30 --lags 5

Outputs metrics (MSE, RMSE, MAE, R2) and directional accuracy, and writes a JSON report next to the model.
"""
import argparse
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    import pymysql
except Exception:
    pymysql = None


def load_data_from_db(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    conn = pymysql.connect(**cfg)
    df = pd.read_sql('SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp', conn)
    conn.close()
    df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


def prepare(df: pd.DataFrame, lags: int = 5):
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['daily_return'] = (df['close_price'] - df['open_price']) / df['open_price']
    for lag in range(1, lags + 1):
        df[f'close_pct_lag_{lag}'] = df['close_price'].pct_change(periods=lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)
    df = df.dropna().reset_index(drop=True)
    return df


def split(df: pd.DataFrame, val_days: int = 30):
    last_ts = df['dt'].max()
    cutoff = last_ts - pd.Timedelta(days=val_days)
    train = df[df['dt'] < cutoff].copy()
    val = df[df['dt'] >= cutoff].copy()
    return train, val


def directional_accuracy(y_true, y_pred):
    return np.mean((np.sign(y_true) == np.sign(y_pred)).astype(float))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--scaler', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--val-days', type=int, default=30)
    parser.add_argument('--lags', type=int, default=5)
    args = parser.parse_args()

    model = joblib.load(args.model)
    scaler = joblib.load(args.scaler)

    df = load_data_from_db(args.config)
    dfp = prepare(df, lags=args.lags)
    train, val = split(dfp, val_days=args.val_days)

    feat_cols = []
    for lag in range(1, args.lags + 1):
        feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']

    X_val = val[feat_cols].values
    y_val = val['daily_return'].values
    Xs = scaler.transform(X_val)
    y_pred = model.predict(Xs)

    mse = mean_squared_error(y_val, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred)
    dacc = directional_accuracy(y_val, y_pred)

    report = {
        'mse': float(mse),
        'rmse': float(rmse),
        'mae': float(mae),
        'r2': float(r2),
        'directional_accuracy': float(dacc),
        'n_val': int(len(y_val))
    }

    print(json.dumps(report, indent=2))

    out_path = os.path.splitext(args.model)[0] + '.eval.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('Saved evaluation to', out_path)


if __name__ == '__main__':
    main()
