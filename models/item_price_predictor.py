"""
item_price_predictor.py — 单饰品 LGBM 7 天价格预测

复用 models/train_model.py 的特征工程模式，基于 item_kline_day 表数据
训练单饰品 LightGBM 模型，预测 7 天后的卖出价。
"""

import logging
import os
import math
from typing import Optional, Dict, Tuple

import numpy as np
import pandas as pd
import lightgbm as lgb
import pymysql
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

_PREDICTION_HORIZON = 7  # 预测 7 天后价格

# 内存缓存：{market_hash_name: (model, train_columns, last_trained_at)}
_model_cache: Dict[str, Tuple] = {}


def _get_db_connection():
    return pymysql.connect(
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DATABASE"),
        charset=os.getenv("CHARSET", "utf8mb4"),
    )


def _fetch_item_kline(market_hash_name: str, limit: int = 500) -> pd.DataFrame:
    """从 item_kline_day 表读取饰品 K 线数据。"""
    conn = None
    try:
        conn = _get_db_connection()
        sql = (
            "SELECT timestamp, price, buy_price, sell_count, buy_count, "
            "turnover, volume, total_count "
            "FROM item_kline_day "
            "WHERE market_hash_name = %s "
            "ORDER BY timestamp ASC LIMIT %s"
        )
        df = pd.read_sql(sql, conn, params=(market_hash_name, limit))
        return df
    except Exception as e:
        logger.error(f"读取 {market_hash_name} K线数据失败: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    特征工程（与 models/train_model.py 保持一致的模式）。
    """
    if df.empty:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    # 筛掉无效数据
    df = df[df["price"] > 0]

    # 目标变量：7 天后的价格
    df["target"] = df["price"].shift(-_PREDICTION_HORIZON)

    # 时间特征
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month

    # 滞后特征
    for lag in [7, 14, 30]:
        df[f"close_lag_{lag}"] = df["price"].shift(lag)

    # 滑动窗口特征
    for window in [7, 14, 30]:
        df[f"close_rolling_mean_{window}"] = df["price"].rolling(window=window).mean()
        df[f"close_rolling_std_{window}"] = df["price"].rolling(window=window).std()
        df[f"volume_rolling_mean_{window}"] = df["volume"].rolling(window=window).mean()

    # 买卖价差特征
    df["spread"] = df["price"] - df["buy_price"]
    df["spread_ratio"] = df["spread"] / df["price"].replace(0, np.nan)

    # 在售/求购比率
    df["supply_demand_ratio"] = (
        df["sell_count"] / df["buy_count"].replace(0, np.nan)
    )

    df.dropna(inplace=True)
    return df


class ItemPricePredictor:
    def __init__(self):
        self.min_data_points = 30  # 最少需要 30 天数据才能训练

    def train_for_item(self, market_hash_name: str) -> Optional[lgb.LGBMRegressor]:
        """
        为单个饰品训练 LGBM 模型，返回训练好的模型。
        """
        df = _fetch_item_kline(market_hash_name)
        if len(df) < self.min_data_points:
            logger.warning(
                f"饰品 {market_hash_name} 仅有 {len(df)} 条数据，"
                f"低于最小要求 {self.min_data_points}"
            )
            return None

        df = _build_features(df)
        if len(df) < 30:
            logger.warning(f"饰品 {market_hash_name} 特征工程后数据不足: {len(df)}")
            return None

        feature_cols = [
            col
            for col in df.columns
            if col not in ("timestamp", "target", "total_count")
            and df[col].dtype in (np.float64, np.int64, float, int)
        ]

        X = df[feature_cols]
        y = df["target"]

        # 时间序列划分：后 20% 为验证集
        train_size = int(len(X) * 0.8)
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]

        lgb_params = {
            "objective": "regression_l1",
            "metric": "rmse",
            "n_estimators": 500,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 1,
            "verbose": -1,
            "n_jobs": -1,
            "seed": 42,
        }

        model = lgb.LGBMRegressor(**lgb_params)

        if len(X_val) >= 5:
            model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(50, verbose=False)],
            )
            # 微调：用验证集继续训练，需要提供 eval_set
            model.fit(
                X_val,
                y_val,
                init_model=model,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(10, verbose=False)],
            )
        else:
            model.fit(X, y)

        # 缓存模型
        _model_cache[market_hash_name] = (model, feature_cols)

        y_pred_val = model.predict(X_val)
        corr = np.corrcoef(y_val, y_pred_val)[0, 1]
        logger.info(f"饰品 {market_hash_name} 模型训练完成, 验证集 ρ={corr:.4f}, 特征数={len(feature_cols)}")

        return model

    def predict_7d_price(self, market_hash_name: str) -> Optional[float]:
        """
        预测饰品 7 天后的价格。
        先尝试从缓存获取模型，缓存不存在则训练。
        """
        model, feature_cols = _model_cache.get(market_hash_name, (None, None))
        if model is None:
            model = self.train_for_item(market_hash_name)
            if model is None:
                return None
            _, feature_cols = _model_cache.get(market_hash_name, (None, None))

        # 取最新一行数据构造特征
        df = _fetch_item_kline(market_hash_name, limit=100)
        if df.empty:
            return None

        df_feat = _build_features(df)
        if df_feat.empty:
            return None

        last_row = df_feat.iloc[[-1]]
        available_features = [f for f in feature_cols if f in last_row.columns]
        if not available_features:
            return None

        X_pred = last_row[available_features]
        predicted = model.predict(X_pred)[0]
        return round(float(predicted), 2)

    def predict_7d_price_range(
        self, market_hash_name: str
    ) -> Optional[Dict]:
        """
        预测饰品 7 天后的价格及波动区间。
        返回 {predicted, lower, upper, confidence}
        """
        predicted = self.predict_7d_price(market_hash_name)
        if predicted is None:
            return None

        # 用最近 7 天的标准差作为波动范围
        df = _fetch_item_kline(market_hash_name, limit=30)
        if df.empty:
            return {"predicted": predicted, "lower": predicted, "upper": predicted, "confidence": "low"}

        std_7d = float(df["price"].tail(7).std()) if len(df) >= 7 else float(df["price"].std())
        lower = round(predicted - 1.5 * std_7d, 2)
        upper = round(predicted + 1.5 * std_7d, 2)

        # 简单置信度判断
        current_price = float(df["price"].iloc[-1])
        price_change = abs(predicted - current_price) / current_price if current_price > 0 else 0
        if price_change < 0.03:
            confidence = "high"
        elif price_change < 0.08:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "predicted": predicted,
            "lower": max(lower, 0.01),
            "upper": upper,
            "confidence": confidence,
        }

    def batch_predict(
        self, market_hash_names: list[str]
    ) -> Dict[str, Optional[float]]:
        """批量预测多个饰品的 7 天后价格。"""
        results = {}
        for name in market_hash_names:
            try:
                results[name] = self.predict_7d_price(name)
            except Exception as e:
                logger.error(f"预测 {name} 失败: {e}")
                results[name] = None
        return results


# 模块级便捷实例
_predictor = ItemPricePredictor()


def predict_item_7d(market_hash_name: str) -> Optional[float]:
    return _predictor.predict_7d_price(market_hash_name)


def predict_item_7d_range(market_hash_name: str) -> Optional[Dict]:
    return _predictor.predict_7d_price_range(market_hash_name)


def batch_predict_items(names: list[str]) -> Dict[str, Optional[float]]:
    return _predictor.batch_predict(names)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    predictor = ItemPricePredictor()

    if len(sys.argv) > 1:
        name = sys.argv[1]
        result = predictor.predict_7d_price_range(name)
        if result:
            print(f"饰品: {name}")
            print(f"  预测 7 天后价格: {result['predicted']}")
            print(f"  价格区间: {result['lower']} ~ {result['upper']}")
            print(f"  置信度: {result['confidence']}")
        else:
            print(f"无法预测 {name}（数据不足或训练失败）")
    else:
        print("用法: python -m models.item_price_predictor <market_hash_name>")
