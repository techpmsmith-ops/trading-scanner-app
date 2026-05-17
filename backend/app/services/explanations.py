from app.config import SETUP_DISCLAIMER


def build_explanation(symbol: str, scores: dict, indicators: dict, setups: list[str], risk_flags: list[str]) -> str:
    close = indicators["close"]
    rsi = indicators.get("rsi_14")
    rel_volume = indicators.get("relative_volume")
    trend_parts = []
    if indicators.get("sma_50") and close > indicators["sma_50"]:
        trend_parts.append("above its 50-day moving average")
    if indicators.get("sma_200") and close > indicators["sma_200"]:
        trend_parts.append("above its 200-day moving average")
    if not trend_parts:
        trend_parts.append("not showing a clean moving-average uptrend")

    setup_text = ", ".join([s for s in setups if s != "Risk Warning / Avoid"]) or "no clear bullish setup"
    risk_text = f" Risk flags: {', '.join(risk_flags)}." if risk_flags else " No major scanner risk flags were detected."
    rsi_text = f" RSI is {rsi:.1f}" if rsi is not None else " RSI is unavailable"
    volume_text = f"relative volume is {rel_volume:.2f}x" if rel_volume is not None else "relative volume is unavailable"

    return (
        f"{symbol} scored {scores['score_total']}/100. The ticker is trading "
        f"{' and '.join(trend_parts)}, based on the latest close. {rsi_text}, and "
        f"{volume_text}. The setup classification is: {setup_text}.{risk_text} "
        f"{SETUP_DISCLAIMER}"
    )
