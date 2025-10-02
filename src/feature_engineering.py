"""
Feature Engineering Module

Handles feature engineering for prediction models.
"""
import pandas as pd
from typing import Tuple, List


def build_features(df: pd.DataFrame, lags: int = 5) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build lag features for prediction model.

    Args:
        df: DataFrame with kline data
        lags: Number of lag periods to create (default: 5)

    Returns:
        Tuple of (featurized DataFrame, list of feature column names)
    """
    df = df.copy()
    
    # Create lag features
    for lag in range(1, lags + 1):
        df[f'close_pct_lag_{lag}'] = df['close_price'].pct_change(periods=lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)
    
    # Build feature column list
    feat_cols = []
    for lag in range(1, lags + 1):
        feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']
    
    # Drop rows with NaN values
    df = df.dropna().reset_index(drop=True)
    
    return df, feat_cols
