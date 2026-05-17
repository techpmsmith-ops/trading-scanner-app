from app.services.indicators import calculate_indicators, latest_indicator_snapshot


def test_indicator_calculations_have_required_fields(sample_bars):
    df = calculate_indicators(sample_bars)
    latest = df.iloc[-1]

    assert latest["ema_20"] > 0
    assert latest["sma_50"] > 0
    assert latest["sma_200"] > 0
    assert latest["atr_14"] > 0
    assert latest["relative_volume"] > 0


def test_latest_snapshot_handles_long_term_structure(sample_bars):
    snapshot = latest_indicator_snapshot(sample_bars)

    assert snapshot["high_52_week"] is not None
    assert snapshot["distance_from_52_week_high"] <= 0
    assert snapshot["close"] > snapshot["sma_200"]
