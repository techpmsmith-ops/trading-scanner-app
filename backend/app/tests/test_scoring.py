from app.services.risk_reward import estimate_risk_reward
from app.services.scoring import classify_setups, score_result


def strong_indicators():
    return {
        "close": 125.0,
        "open": 124.0,
        "ema_20": 123.0,
        "sma_50": 118.0,
        "sma_200": 105.0,
        "ema_20_slope": 2.0,
        "sma_50_slope": 3.0,
        "rsi_14": 62.0,
        "macd_line": 1.4,
        "macd_signal": 1.0,
        "macd_histogram": 0.4,
        "atr_14": 3.0,
        "atr_percent": 2.4,
        "avg_volume_20": 2_000_000,
        "relative_volume": 1.35,
        "high_20": 126.0,
        "low_20": 116.0,
        "high_52_week": 130.0,
        "low_52_week": 90.0,
    }


def test_setup_classification_breakout_and_momentum():
    setups, flags = classify_setups(strong_indicators())

    assert "Breakout Candidate" in setups
    assert "Momentum Strength" in setups
    assert flags == []


def test_scoring_returns_transparent_components():
    indicators = strong_indicators()
    setups, flags = classify_setups(indicators)
    score = score_result(indicators, setups, flags)

    assert 0 <= score["score_total"] <= 100
    assert score["score_trend"] > 0
    assert score["score_setup_quality"] >= 11


def test_risk_reward_estimate_has_positive_ratio():
    indicators = strong_indicators()
    estimate = estimate_risk_reward(indicators, ["Breakout Candidate"])

    assert estimate["entry_zone"] > 0
    assert estimate["stop_loss"] < estimate["entry_zone"]
    assert estimate["target_2"] > estimate["entry_zone"]
    assert estimate["risk_reward"] > 0


def test_missing_or_weak_data_gets_risk_flags():
    indicators = strong_indicators()
    indicators.update(close=80.0, sma_200=120.0, avg_volume_20=100_000, atr_percent=12.0, rsi_14=82.0)
    setups, flags = classify_setups(indicators)

    assert "Risk Warning / Avoid" in setups
    assert "Very low volume" in flags
    assert "ATR percentage too high" in flags
