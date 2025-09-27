import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    # scipy v1.7+ exposes binomtest
    from scipy.stats import binomtest as _binomtest
    def binom_test(k, n, p=0.5, alternative='greater'):
        res = _binomtest(k, n, p=p, alternative=alternative)
        return res.pvalue
except Exception:
    try:
        # older scipy exposes binom_test
        from scipy.stats import binom_test as _binom_test
        def binom_test(k, n, p=0.5, alternative='greater'):
            # binom_test in older scipy returns p-value directly
            return _binom_test(k, n, p=p, alternative=alternative)
    except Exception:
        # fallback: use survival function approximation
        import math
        def binom_test(k, n, p=0.5, alternative='greater'):
            # very rough normal approx
            mean = n * p
            var = n * p * (1 - p)
            if var == 0:
                return 1.0
            z = (k - mean) / math.sqrt(var)
            # one-sided pvalue
            from math import erf
            pval = 0.5 * (1 - erf(z / math.sqrt(2)))
            return pval
from sklearn.metrics import mean_squared_error, mean_absolute_error

MODELS_DIR = 'models'
CFG = 'config.json'


def load_fold_predictions(model_path, scaler_path, df, feat_cols):
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    X = df[feat_cols].values
    Xs = scaler.transform(X)
    preds = model.predict(Xs)
    return preds


def baseline_predictions(df):
    # zero baseline
    zero_pred = np.zeros(len(df))
    # last-day baseline: predict today's return = yesterday's return
    last_day = df['daily_return'].shift(1).fillna(0).values
    return {'zero': zero_pred, 'last': last_day}


def directional_acc(y_true, y_pred):
    return float((np.sign(y_true) == np.sign(y_pred)).mean())


def backtest_returns(y_true, y_pred, open_price, fee=0.001, slippage=0.001):
    # simple strategy: go long if pred>0 else short if pred<0; position size = 1
    sig = np.sign(y_pred)
    # gross return per trade = sig * y_true
    gross = sig * y_true
    # cost approximate as fee + slippage applied to trade not to return; estimate cost fraction = fee+slippage
    cost = (fee + slippage) * np.ones_like(gross)
    net = gross - cost * np.abs(sig)
    # cumulative returns series
    cum = np.cumsum(net)
    return net, cum


def analyze():
    summary = json.load(open(os.path.join(MODELS_DIR, 'lgb_walkforward_summary.json'), 'r', encoding='utf-8'))
    folds = summary['folds']

    report = {'folds': []}

    # Reconstruct per-fold predictions by re-running on validation sets
    # We need original data
    with open(CFG, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    import pymysql
    conn = pymysql.connect(**cfg)
    df_all = pd.read_sql('SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp', conn)
    conn.close()
    df_all['dt'] = pd.to_datetime(df_all['timestamp'], unit='s')

    for i, fmeta in enumerate(folds):
        # load feature importance file to get feature list
        fi_path = os.path.join(MODELS_DIR, f'fi_fold{i}_')
        # instead, we will reconstruct features and use same feat order as training script
        dfp = df_all.copy()
        # build features
        lags = 5
        for lag in range(1, lags + 1):
            dfp[f'close_pct_lag_{lag}'] = dfp['close_price'].pct_change(periods=lag)
            dfp[f'vol_lag_{lag}'] = dfp['volume'].shift(lag)
        for w in [5,10,20]:
            dfp[f'close_mean_{w}'] = dfp['close_price'].rolling(window=w).mean()
            dfp[f'close_std_{w}'] = dfp['close_price'].rolling(window=w).std()
        dfp['daily_return'] = (dfp['close_price'] - dfp['open_price']) / dfp['open_price']
        dfp = dfp.dropna().reset_index(drop=True)

        # determine validation slice by matching val_end in metadata
        val_end = pd.to_datetime(fmeta['val_end'])
        val_start = pd.to_datetime(fmeta['train_end'])
        val_mask = (dfp['dt'] >= val_start) & (dfp['dt'] < val_end)
        val_df = dfp[val_mask].copy()
        feat_cols = []
        for lag in range(1, lags + 1):
            feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']
        for w in [5,10,20]:
            feat_cols += [f'close_mean_{w}', f'close_std_{w}']

        model_path = os.path.join(MODELS_DIR, f'lgb_fold{i}_')
        # find exact model file
        mfiles = [x for x in os.listdir(MODELS_DIR) if x.startswith(f'lgb_fold{i}_') and x.endswith('.joblib')]
        sfiles = [x for x in os.listdir(MODELS_DIR) if x.startswith(f'scaler_fold{i}_') and x.endswith('.joblib')]
        if not mfiles or not sfiles:
            continue
        model_path = os.path.join(MODELS_DIR, mfiles[0])
        scaler_path = os.path.join(MODELS_DIR, sfiles[0])

        preds = load_fold_predictions(model_path, scaler_path, val_df, feat_cols)

        # Baselines
        baselines = baseline_predictions(val_df)
        fold_report = {'fold': i, 'n_val': len(val_df)}
        for name, bpred in baselines.items():
            mse = mean_squared_error(val_df['daily_return'].values, bpred[:len(val_df)])
            dacc = directional_acc(val_df['daily_return'].values, bpred[:len(val_df)])
            fold_report[f'baseline_{name}_mse'] = float(mse)
            fold_report[f'baseline_{name}_dacc'] = float(dacc)

        # model metrics
        mse = mean_squared_error(val_df['daily_return'].values, preds)
        dacc = directional_acc(val_df['daily_return'].values, preds)
        fold_report.update({'model_mse': float(mse), 'model_dacc': float(dacc)})

        # binomial test for direction
        successes = int((np.sign(val_df['daily_return'].values) == np.sign(preds)).sum())
        pval = binom_test(successes, n=len(preds), p=0.5, alternative='greater')
        fold_report['direction_binom_pval'] = float(pval)

        # backtest
        net, cum = backtest_returns(val_df['daily_return'].values, preds, val_df['open_price'].values, fee=0.001, slippage=0.001)
        # basic stats
        total_return = float(np.sum(net))
        ann_return = total_return / (len(net) / 252) if len(net) > 0 else 0.0
        sharpe = float(np.mean(net) / (np.std(net) + 1e-9) * np.sqrt(252)) if np.std(net) > 0 else 0.0
        max_dd = float(np.max(np.maximum.accumulate(np.cumsum(net)) - np.cumsum(net)))
        # Apply user-specified final-asset loss of 3.6%: final_assets = 1 + cumulative_net; profit = final_assets*0.964 - 1
        final_assets = 1.0 + (cum[-1] if len(cum) > 0 else 0.0)
        profit_after_3_6pct = float(final_assets * 0.964 - 1.0)
        fold_report.update({'backtest_total': total_return, 'backtest_annualized': ann_return, 'backtest_sharpe': sharpe, 'backtest_maxdd': max_dd, 'backtest_profit_after_3.6pct': profit_after_3_6pct})

        # save cum plot
        plt.figure()
        plt.plot(cum)
        plt.title(f'Fold {i} cumulative P&L (net)')
        plt.xlabel('step')
        plt.ylabel('cumulative net return')
        plt.grid(True)
        plt.savefig(os.path.join(MODELS_DIR, f'fold{i}_cum.png'))
        plt.close()

        # fold 3 diagnostics
        if i == 3:
            # pred vs true
            plt.figure()
            plt.plot(val_df['dt'].values, val_df['daily_return'].values, label='true')
            plt.plot(val_df['dt'].values, preds, label='pred')
            plt.legend()
            plt.title('Fold 3: true vs pred')
            plt.savefig(os.path.join(MODELS_DIR, 'fold3_true_pred.png'))
            plt.close()

            # residuals
            res = val_df['daily_return'].values - preds
            plt.figure()
            plt.hist(res, bins=50)
            plt.title('Fold 3 residuals')
            plt.savefig(os.path.join(MODELS_DIR, 'fold3_residuals.png'))
            plt.close()

            # rolling volatility comparison
            vol_window = 20
            val_df['true_abs'] = np.abs(val_df['daily_return'])
            val_df['rolling_vol_true'] = val_df['true_abs'].rolling(window=vol_window).std()
            val_df['rolling_vol_pred'] = pd.Series(np.abs(preds)).rolling(window=vol_window).std()
            plt.figure()
            plt.plot(val_df['dt'].values, val_df['rolling_vol_true'], label='true vol')
            plt.plot(val_df['dt'].values, val_df['rolling_vol_pred'], label='pred vol')
            plt.legend()
            plt.title('Fold 3 rolling vol (window=20)')
            plt.savefig(os.path.join(MODELS_DIR, 'fold3_vol.png'))
            plt.close()

        report['folds'].append(fold_report)

    # aggregate report
    with open(os.path.join(MODELS_DIR, 'analysis_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    analyze()
