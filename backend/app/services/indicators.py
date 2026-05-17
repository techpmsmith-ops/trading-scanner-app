import pandas as pd


def calculate_indicators(bars: pd.DataFrame) -> pd.DataFrame:
    df = bars.copy().sort_values("date")
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    df["ema_20"] = close.ewm(span=20, adjust=False).mean()
    df["sma_50"] = close.rolling(50).mean()
    df["sma_200"] = close.rolling(200).mean()
    df["ema_20_slope"] = df["ema_20"].diff(5)
    df["sma_50_slope"] = df["sma_50"].diff(5)

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema_12 - ema_26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["macd_signal"]

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    df["atr_14"] = true_range.rolling(14).mean()
    df["atr_percent"] = (df["atr_14"] / close) * 100

    df["avg_volume_20"] = volume.rolling(20).mean()
    df["relative_volume"] = volume / df["avg_volume_20"]
    df["high_20"] = high.rolling(20).max()
    df["low_20"] = low.rolling(20).min()
    df["high_52_week"] = high.rolling(252, min_periods=200).max()
    df["low_52_week"] = low.rolling(252, min_periods=200).min()
    df["distance_from_20_high"] = ((close - df["high_20"]) / df["high_20"]) * 100
    df["distance_from_52_week_high"] = ((close - df["high_52_week"]) / df["high_52_week"]) * 100
    return df


def latest_indicator_snapshot(bars: pd.DataFrame) -> dict:
    df = calculate_indicators(bars)
    latest = df.iloc[-1]
    keys = [
        "ema_20", "sma_50", "sma_200", "ema_20_slope", "sma_50_slope",
        "rsi_14", "macd_line", "macd_signal", "macd_histogram", "atr_14",
        "atr_percent", "avg_volume_20", "relative_volume", "high_20", "low_20",
        "high_52_week", "low_52_week", "distance_from_20_high",
        "distance_from_52_week_high",
    ]
    snapshot = {key: _safe_float(latest.get(key)) for key in keys}
    snapshot.update(
        close=_safe_float(latest["close"]),
        open=_safe_float(latest["open"]),
        high=_safe_float(latest["high"]),
        low=_safe_float(latest["low"]),
        volume=int(latest["volume"]),
        date=str(latest["date"]),
    )
    return snapshot


def _safe_float(value):
    if pd.isna(value):
        return None
    return round(float(value), 4)
