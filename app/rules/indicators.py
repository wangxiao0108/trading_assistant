from __future__ import annotations

import pandas as pd


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ma5"] = result["close"].rolling(window=5).mean()
    result["ma13"] = result["close"].rolling(window=13).mean()
    result["ma20"] = result["close"].rolling(window=20).mean()
    result["vol_ma5"] = result["volume"].rolling(window=5).mean()
    result["vol_ma20"] = result["volume"].rolling(window=20).mean()
    return result


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / previous * 100
