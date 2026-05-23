from statistics import mean

import yfinance as yf

from app.services.logging import log_warning

POSITIVE_WORDS = {
    "beat", "beats", "bullish", "upgrade", "upgraded", "growth", "strong", "surge", "surges",
    "gain", "gains", "record", "outperform", "optimistic", "profit", "profits", "rally", "raises",
}
NEGATIVE_WORDS = {
    "miss", "misses", "bearish", "downgrade", "downgraded", "weak", "weakness", "drop", "drops",
    "loss", "losses", "lawsuit", "probe", "concern", "concerns", "risk", "cuts", "slump", "falls",
}


def score_symbol_news(symbol: str) -> dict:
    try:
        items = yf.Ticker(symbol).news or []
    except Exception as exc:
        log_warning("news_sentiment_failed", symbol=symbol, error=str(exc))
        return {"score": 0.0, "label": "neutral", "headline_count": 0, "headlines": []}

    headlines = []
    scores = []
    for item in items[:10]:
        title = _title(item)
        if not title:
            continue
        headlines.append(title)
        scores.append(_score_text(title))
    score = round(mean(scores), 3) if scores else 0.0
    return {
        "score": score,
        "label": _label(score),
        "headline_count": len(headlines),
        "headlines": headlines[:5],
    }


def _title(item: dict) -> str:
    content = item.get("content") if isinstance(item, dict) else None
    if isinstance(content, dict) and content.get("title"):
        return str(content["title"])
    return str(item.get("title", "")) if isinstance(item, dict) else ""


def _score_text(text: str) -> float:
    tokens = {token.strip(".,:;!?()[]{}\"'").lower() for token in text.split()}
    positive = len(tokens & POSITIVE_WORDS)
    negative = len(tokens & NEGATIVE_WORDS)
    total = positive + negative
    if total == 0:
        return 0.0
    return (positive - negative) / total


def _label(score: float) -> str:
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"
