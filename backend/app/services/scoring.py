from app.config import KRONOS_WEIGHT, MAX_ATR_PERCENT, MIN_AVG_VOLUME

DEFAULT_COMPONENT_WEIGHTS = {
    "trend": 1.0,
    "momentum": 1.0,
    "volume": 1.0,
    "risk": 1.0,
    "setup_quality": 1.0,
}


def classify_setups(indicators: dict) -> tuple[list[str], list[str]]:
    close = indicators["close"]
    ema_20 = indicators.get("ema_20")
    sma_50 = indicators.get("sma_50")
    sma_200 = indicators.get("sma_200")
    rsi = indicators.get("rsi_14")
    rel_volume = indicators.get("relative_volume") or 0
    atr_pct = indicators.get("atr_percent") or 0
    macd_hist = indicators.get("macd_histogram")
    high_20 = indicators.get("high_20")
    sma_50_slope = indicators.get("sma_50_slope") or 0
    avg_volume = indicators.get("avg_volume_20") or 0
    open_price = indicators.get("open") or close

    setups: list[str] = []
    flags: list[str] = []

    if all(v is not None for v in [ema_20, sma_50, sma_200, rsi]):
        near_ema_20 = abs(close - ema_20) / close <= 0.03
        if close > sma_50 and close > sma_200 and ema_20 > sma_50 and 40 <= rsi <= 60 and near_ema_20 and sma_50_slope > 0:
            setups.append("Trend Continuation Pullback")

    if all(v is not None for v in [high_20, sma_50, sma_200, rsi]):
        near_high_20 = (high_20 - close) / high_20 <= 0.03
        if near_high_20 and rel_volume > 1.2 and close > sma_50 and close > sma_200 and 55 <= rsi <= 75:
            setups.append("Breakout Candidate")

    if all(v is not None for v in [ema_20, sma_50, macd_hist, rsi]):
        if close > ema_20 and close > sma_50 and macd_hist > 0 and 55 <= rsi <= 75 and rel_volume > 1.0:
            setups.append("Momentum Strength")

    if all(v is not None for v in [ema_20, sma_200, rsi]):
        not_too_far_below_200 = close >= sma_200 * 0.9
        if rsi < 35 and close < ema_20 and not_too_far_below_200 and atr_pct < MAX_ATR_PERCENT:
            setups.append("Oversold Bounce Watch")

    if avg_volume and avg_volume < MIN_AVG_VOLUME:
        flags.append("Very low volume")
    if atr_pct and atr_pct > MAX_ATR_PERCENT:
        flags.append("ATR percentage too high")
    if sma_200 and close < sma_200 * 0.9:
        flags.append("Close far below 200 SMA")
    if rsi and rsi > 78:
        flags.append("RSI overextended")
    if ema_20 and sma_50 and close < ema_20 and close > sma_50:
        flags.append("Conflicting short-term trend")
    if open_price and abs(close - open_price) / open_price > 0.05 and rel_volume < 1.0:
        flags.append("Large candle without volume confirmation")
    if not setups:
        flags.append("No clear Stage 1 setup")

    if flags:
        setups.append("Risk Warning / Avoid")
    return list(dict.fromkeys(setups)), list(dict.fromkeys(flags))


def score_result(
    indicators: dict,
    setups: list[str],
    risk_flags: list[str],
    component_weights: dict | None = None,
    kronos_signal: dict | None = None,
) -> dict:
    weights = {**DEFAULT_COMPONENT_WEIGHTS, **(component_weights or {})}
    close = indicators["close"]
    ema_20 = indicators.get("ema_20")
    sma_50 = indicators.get("sma_50")
    sma_200 = indicators.get("sma_200")
    rsi = indicators.get("rsi_14")
    macd_line = indicators.get("macd_line")
    macd_signal = indicators.get("macd_signal")
    macd_hist = indicators.get("macd_histogram")
    rel_volume = indicators.get("relative_volume") or 0
    avg_volume = indicators.get("avg_volume_20") or 0
    atr_pct = indicators.get("atr_percent") or 0

    trend = 0
    trend += 7 if ema_20 and close > ema_20 else 0
    trend += 8 if sma_50 and close > sma_50 else 0
    trend += 8 if sma_200 and close > sma_200 else 0
    trend += 4 if ema_20 and sma_50 and ema_20 > sma_50 else 0
    trend += 3 if (indicators.get("sma_50_slope") or 0) > 0 else 0

    momentum = 0
    momentum += 8 if rsi and 50 <= rsi <= 70 else 0
    momentum += 6 if macd_hist and macd_hist > 0 else 0
    momentum += 4 if macd_line and macd_signal and macd_line > macd_signal else 0
    momentum += 2 if rsi and rsi < 80 else 0

    volume = 0
    volume += 5 if rel_volume > 1.0 else 0
    volume += 5 if rel_volume > 1.2 else 0
    volume += 5 if avg_volume > MIN_AVG_VOLUME else 0

    risk = 0
    risk += 8 if 1 <= atr_pct <= 5 else 0
    risk += 4 if atr_pct < 8 else 0
    risk += 3 if not any(flag in risk_flags for flag in ["ATR percentage too high", "Large candle without volume confirmation"]) else 0

    quality = 0
    quality += 7 if "Breakout Candidate" in setups else 0
    quality += 7 if "Trend Continuation Pullback" in setups else 0
    quality += 4 if "Momentum Strength" in setups else 0
    quality += 2 if any(s in setups for s in ["Breakout Candidate", "Trend Continuation Pullback", "Momentum Strength", "Oversold Bounce Watch"]) else 0

    weighted_total = (
        trend * float(weights.get("trend", 1.0))
        + momentum * float(weights.get("momentum", 1.0))
        + volume * float(weights.get("volume", 1.0))
        + risk * float(weights.get("risk", 1.0))
        + quality * float(weights.get("setup_quality", 1.0))
    )
    base_total = max(0, min(100, round(weighted_total - max(0, len(risk_flags) - 1) * 3)))
    kronos_score = _score_kronos_signal(kronos_signal)
    if kronos_score is None:
        total = base_total
        kronos_score = 0
    else:
        weight = min(0.5, max(0.0, KRONOS_WEIGHT))
        total = round((base_total * (1 - weight)) + (kronos_score * weight))
    return {
        "score_trend": trend,
        "score_momentum": momentum,
        "score_volume": volume,
        "score_risk": risk,
        "score_setup_quality": quality,
        "score_kronos": int(kronos_score),
        "score_total": total,
    }


def _score_kronos_signal(kronos_signal: dict | None) -> int | None:
    if not kronos_signal or kronos_signal.get("kronos_bias") == "unavailable":
        return None
    confidence = float(kronos_signal.get("kronos_confidence") or 0)
    bias = kronos_signal.get("kronos_bias")
    if bias == "bullish":
        return int(min(100, max(50, confidence)))
    if bias == "neutral":
        return int(min(75, max(35, 50 + confidence * 0.1)))
    if bias == "bearish":
        return int(max(0, 50 - confidence * 0.5))
    return None
