"""
LightGBM walk-forward pipeline for day-return prediction.

Configuration (defaults):
- train_window = 365 days
- val_window = 90 days
- step = 90 days

脚本会保存每个 fold 的模型、feature importance 和评估报告到 models/
"""
import os
import json
import time
import joblib
import argparse
from typing import List

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    import pymysql
except Exception:
    pymysql = None


def load_df_from_db(config_path: str) -> pd.DataFrame:
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    conn = pymysql.connect(**cfg)
    df = pd.read_sql('SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp', conn)
    conn.close()
    df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


def featurize(df: pd.DataFrame, lags: int = 5) -> pd.DataFrame:
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['daily_return'] = (df['close_price'] - df['open_price']) / df['open_price']

    # lags
    for lag in range(1, lags + 1):
        df[f'close_pct_lag_{lag}'] = df['close_price'].pct_change(periods=lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)

    # rolling features
    for w in [5, 10, 20]:
        df[f'close_mean_{w}'] = df['close_price'].rolling(window=w).mean()
        df[f'close_std_{w}'] = df['close_price'].rolling(window=w).std()

    df = df.dropna().reset_index(drop=True)
    return df


def walk_forward_splits(df: pd.DataFrame, train_window: int, val_window: int, step: int):
    # df indexed by datetime in column 'dt'
    last_date = df['dt'].max()
    start_date = df['dt'].min()
    splits = []
    train_start = start_date
    while True:
        train_end = train_start + pd.Timedelta(days=train_window)
        val_end = train_end + pd.Timedelta(days=val_window)
        if val_end > last_date:
            break
        train_idx = (df['dt'] >= train_start) & (df['dt'] < train_end)
        val_idx = (df['dt'] >= train_end) & (df['dt'] < val_end)
        splits.append((train_idx, val_idx, train_start, train_end, val_end))
        train_start = train_start + pd.Timedelta(days=step)
    return splits


def evaluate(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    dacc = float((np.sign(y_true) == np.sign(y_pred)).mean())
    return {'mse': float(mse), 'rmse': float(rmse), 'mae': float(mae), 'r2': float(r2), 'directional_accuracy': dacc}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--out-dir', default='models')
    parser.add_argument('--lags', type=int, default=5)
    parser.add_argument('--train-window', type=int, default=365)
    parser.add_argument('--val-window', type=int, default=90)
    parser.add_argument('--step', type=int, default=90)
    args = parser.parse_args()

    if pymysql is None:
        raise RuntimeError('pymysql required to read from DB')

    df = load_df_from_db(args.config)
    dfp = featurize(df, lags=args.lags)

    feat_cols = []
    for lag in range(1, args.lags + 1):
        feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']
    for w in [5,10,20]:
        feat_cols += [f'close_mean_{w}', f'close_std_{w}']

    splits = walk_forward_splits(dfp, args.train_window, args.val_window, args.step)
    print(f'Creating {len(splits)} folds')

    os.makedirs(args.out_dir, exist_ok=True)
    fold_reports = []
    for i, (train_idx, val_idx, ts, te, ve) in enumerate(splits):
        train = dfp[train_idx].copy()
        val = dfp[val_idx].copy()

        X_train = train[feat_cols].values
        y_train = train['daily_return'].values
        X_val = val[feat_cols].values
        y_val = val['daily_return'].values

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)

        lgb_train = lgb.Dataset(X_train_s, label=y_train)
        lgb_val = lgb.Dataset(X_val_s, label=y_val, reference=lgb_train)

        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'verbose': -1
        }

        # Use callbacks for early stopping and to suppress log output for compatibility
        callbacks = [lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)]
        bst = lgb.train(params, lgb_train, num_boost_round=1000, valid_sets=[lgb_val], callbacks=callbacks)
        y_pred = bst.predict(X_val_s, num_iteration=bst.best_iteration)
        rpt = evaluate(y_val, y_pred)
        rpt.update({'fold': i, 'train_start': str(ts), 'train_end': str(te), 'val_end': str(ve), 'n_train': len(y_train), 'n_val': len(y_val)})
        fold_reports.append(rpt)

        # save model, scaler and feature importance
        model_path = os.path.join(args.out_dir, f'lgb_fold{i}_{int(time.time())}.joblib')
        scaler_path = os.path.join(args.out_dir, f'scaler_fold{i}_{int(time.time())}.joblib')
        joblib.dump(bst, model_path)
        joblib.dump(scaler, scaler_path)

        fi = bst.feature_importance(importance_type='gain')
        fi_df = pd.DataFrame({'feature': feat_cols, 'importance': fi}).sort_values('importance', ascending=False)
        fi_df.to_csv(os.path.join(args.out_dir, f'fi_fold{i}_{int(time.time())}.csv'), index=False)

        print(f'Fold {i} done: val_n={len(y_val)} mse={rpt["mse"]:.6f} dir_acc={rpt["directional_accuracy"]:.3f}')

    # aggregate
    rpt_df = pd.DataFrame(fold_reports)
    agg = rpt_df[['mse','rmse','mae','r2','directional_accuracy']].agg(['mean','std']).to_dict()
    with open(os.path.join(args.out_dir, 'lgb_walkforward_summary.json'), 'w', encoding='utf-8') as f:
        json.dump({'folds': fold_reports, 'aggregate': agg}, f, ensure_ascii=False, indent=2)

    print('Walk-forward training complete. Summary saved to models/lgb_walkforward_summary.json')


if __name__ == '__main__':
    main()
