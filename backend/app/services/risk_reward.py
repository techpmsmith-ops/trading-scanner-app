def estimate_risk_reward(indicators: dict, setups: list[str]) -> dict:
    close = indicators["close"]
    ema_20 = indicators.get("ema_20") or close
    high_20 = indicators.get("high_20") or close
    low_20 = indicators.get("low_20") or close
    atr = indicators.get("atr_14") or max(close * 0.02, 0.01)

    if "Breakout Candidate" in setups:
        entry = high_20 * 1.001
        stop = min(ema_20, low_20)
        risk = max(entry - stop, atr)
        target_1 = entry + risk
        target_2 = entry + (2 * risk)
    elif "Trend Continuation Pullback" in setups:
        entry = max(ema_20, close)
        stop = min(low_20, entry - 1.5 * atr)
        risk = max(entry - stop, atr)
        target_1 = high_20
        target_2 = high_20 + atr
    elif "Oversold Bounce Watch" in setups:
        entry = close
        stop = close - 1.25 * atr
        risk = max(entry - stop, atr)
        target_1 = ema_20
        target_2 = ema_20 + atr
    else:
        entry = close
        stop = close - 1.5 * atr
        risk = max(entry - stop, atr)
        target_1 = close + risk
        target_2 = close + (2 * risk)

    reward = target_2 - entry
    risk_reward = reward / risk if risk > 0 else None
    return {
        "entry_zone": round(entry, 2),
        "stop_loss": round(stop, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "risk_reward": round(risk_reward, 2) if risk_reward is not None else None,
    }
