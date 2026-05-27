from time import perf_counter

import pandas as pd

from app.config import KRONOS_ENABLED, KRONOS_FORECAST_BARS, KRONOS_MODEL_NAME
from app.services.kronos.kronos_adapter import dataframe_to_kronos_bars, unavailable_result
from app.services.kronos.kronos_client import get_kronos_client
from app.services.kronos.kronos_schema import KronosBar, KronosSignal
from app.services.kronos.kronos_signal_mapper import map_forecast_to_signal
from app.services.logging import log_event, log_warning


def forecast_signal(symbol: str, timeframe: str, bars: pd.DataFrame | list[KronosBar], forecast_bars: int | None = None) -> KronosSignal:
    if isinstance(bars, pd.DataFrame):
        input_bars = dataframe_to_kronos_bars(bars)
    else:
        input_bars = bars

    if not KRONOS_ENABLED:
        forecast = unavailable_result(symbol, timeframe, KRONOS_MODEL_NAME, "Kronos is disabled.")
        return map_forecast_to_signal(forecast, input_bars[-1].close if input_bars else 0)

    started = perf_counter()
    try:
        forecast = get_kronos_client().predict(symbol, timeframe, input_bars, forecast_bars or KRONOS_FORECAST_BARS)
        duration = round(perf_counter() - started, 3)
        log_event(
            "kronos_forecast_completed",
            symbol=symbol,
            bars_used=forecast.lookback_bars_used,
            model=forecast.model_name,
            inference_duration_seconds=duration,
            success=forecast.error is None,
            error=forecast.error,
        )
        return map_forecast_to_signal(forecast, input_bars[-1].close if input_bars else 0)
    except Exception as exc:
        duration = round(perf_counter() - started, 3)
        log_warning(
            "kronos_forecast_failed",
            symbol=symbol,
            model=KRONOS_MODEL_NAME,
            inference_duration_seconds=duration,
            error=str(exc),
        )
        forecast = unavailable_result(symbol, timeframe, KRONOS_MODEL_NAME, str(exc))
        return map_forecast_to_signal(forecast, input_bars[-1].close if input_bars else 0)


def signal_to_scan_fields(signal: KronosSignal, enabled: bool = KRONOS_ENABLED) -> dict:
    forecast = signal.forecast
    expected_range = forecast.predicted_high_low_range or {}
    return {
        "kronos_enabled": enabled,
        "kronos_model_name": forecast.model_name,
        "kronos_bias": signal.kronos_bias,
        "kronos_confidence": signal.kronos_confidence,
        "kronos_expected_range_low": expected_range.get("low"),
        "kronos_expected_range_high": expected_range.get("high"),
        "kronos_volatility_estimate": forecast.volatility_estimate,
        "kronos_summary": signal.kronos_summary,
        "kronos_raw_output_json": forecast.model_dump(mode="json"),
        "kronos_error": forecast.error,
    }
