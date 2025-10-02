"""
Predictor Module

Handles market predictions using trained models.
"""
import pandas as pd
from typing import List, Dict, Any


def predict_next_days(model, scaler, df: pd.DataFrame, feat_cols: List[str], days: int = 5) -> List[Dict[str, Any]]:
    """
    Predict market movements for the next N days.

    Args:
        model: Trained prediction model
        scaler: Feature scaler
        df: DataFrame with featurized historical data
        feat_cols: List of feature column names
        days: Number of days to predict (default: 5)

    Returns:
        List of prediction dictionaries with keys: 'day', 'predicted_daily_return', 'direction'
    """
    cur = df.copy()
    # Use last fully populated row as base
    cur_row = cur.dropna().iloc[-1:].copy()
    results = []
    
    for d in range(1, days + 1):
        # Extract features and make prediction
        X = cur_row[feat_cols].values
        Xs = scaler.transform(X)
        pred = float(model.predict(Xs)[0])
        
        # Store prediction result
        results.append({
            'day': d,
            'predicted_daily_return': pred,
            'direction': 'up' if pred > 0 else ('flat' if pred == 0 else 'down')
        })
        
        # Simulate new row for next prediction
        today_close = float(cur_row['close_price'].values[0])
        sim_close = today_close * (1.0 + pred)
        sim_volume = float(cur_row['volume'].values[0])
        
        new = cur_row.copy()
        new['timestamp'] = int(cur_row['timestamp'].values[0]) + 86400
        new['open_price'] = today_close
        new['close_price'] = sim_close
        new['high_price'] = max(today_close, sim_close)
        new['low_price'] = min(today_close, sim_close)
        new['volume'] = sim_volume
        
        # Rebuild features for next iteration
        hist = pd.concat([cur, new], ignore_index=True)
        for lag in range(1, 6):
            hist[f'close_pct_lag_{lag}'] = hist['close_price'].pct_change(periods=lag)
            hist[f'vol_lag_{lag}'] = hist['volume'].shift(lag)
        
        cur = hist.copy()
        cur_row = cur.dropna().iloc[-1:].copy()
    
    return results
