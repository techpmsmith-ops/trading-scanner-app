from datetime import datetime

import pandas as pd

from app.config import KRONOS_FORECAST_BARS, KRONOS_LOOKBACK_BARS
from app.services.kronos.kronos_schema import KronosBar, KronosForecastResult
from app.services.kronos.kronos_signal_mapper import confidence_from_move, direction_from_path

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


def dataframe_to_kronos_bars(bars: pd.DataFrame) -> list[KronosBar]:
    timestamp_col = "timestamp" if "timestamp" in bars.columns else "date"
    normalized = bars.copy()
    if timestamp_col not in normalized.columns:
        normalized = normalized.reset_index().rename(columns={"index": "timestamp"})
        timestamp_col = "timestamp"
    output = []
    for row in normalized.to_dict("records"):
        amount = row.get("amount")
        output.append(
            KronosBar(
                timestamp=pd.to_datetime(row[timestamp_col]).to_pydatetime(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                amount=float(amount) if amount is not None else None,
            )
        )
    return output


def bars_to_dataframe(bars: list[KronosBar]) -> pd.DataFrame:
    return pd.DataFrame([bar.model_dump() for bar in bars])


def validate_ohlcv(bars: list[KronosBar], lookback_bars: int = KRONOS_LOOKBACK_BARS) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if len(bars) < lookback_bars:
        return False, [f"Insufficient history: {len(bars)} bars available, {lookback_bars} required."]
    seen = set()
    for index, bar in enumerate(bars):
        if bar.timestamp in seen:
            warnings.append(f"Duplicate timestamp at row {index}: {bar.timestamp.isoformat()}")
        seen.add(bar.timestamp)
        if min(bar.open, bar.high, bar.low, bar.close) <= 0:
            return False, [f"Non-positive OHLC value at row {index}."]
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
            return False, [f"Invalid high/low bounds at row {index}."]
        if bar.volume < 0:
            return False, [f"Negative volume at row {index}."]
    return True, warnings


def unavailable_result(symbol: str, timeframe: str, model_name: str, error: str, warnings: list[str] | None = None) -> KronosForecastResult:
    return KronosForecastResult(
        symbol=symbol,
        timeframe=timeframe,
        forecast_horizon=KRONOS_FORECAST_BARS,
        predicted_direction="unavailable",
        confidence_score=0,
        model_name=model_name,
        lookback_bars_used=0,
        warnings=warnings or [],
        error=error,
    )


def build_result_from_prediction(symbol: str, timeframe: str, model_name: str, input_bars: list[KronosBar], prediction: pd.DataFrame) -> KronosForecastResult:
    close_path = [round(float(value), 4) for value in prediction["close"].tolist()] if "close" in prediction else []
    low = round(float(prediction["low"].min()), 4) if "low" in prediction and not prediction.empty else None
    high = round(float(prediction["high"].max()), 4) if "high" in prediction and not prediction.empty else None
    latest_close = input_bars[-1].close
    volatility = None
    if close_path and latest_close:
        volatility = round(((max(close_path) - min(close_path)) / latest_close) * 100, 2)
    direction = direction_from_path(latest_close, close_path)
    confidence = confidence_from_move(latest_close, close_path, volatility)
    return KronosForecastResult(
        symbol=symbol,
        timeframe=timeframe,
        forecast_horizon=len(close_path),
        predicted_direction=direction,
        confidence_score=confidence,
        predicted_close_path=close_path,
        predicted_high_low_range={"low": low, "high": high},
        volatility_estimate=volatility,
        model_name=model_name,
        lookback_bars_used=len(input_bars),
        created_at=datetime.utcnow(),
        raw_output=_prediction_raw_output(prediction),
    )


def _prediction_raw_output(prediction: pd.DataFrame) -> dict:
    if "timestamp" in prediction.columns:
        raw_rows = prediction.copy()
    else:
        raw_rows = prediction.reset_index().rename(columns={"index": "timestamp"})
    for column in raw_rows.columns:
        if "time" in str(column).lower() or str(column) == "timestamp":
            raw_rows[column] = raw_rows[column].astype(str)
    return {"columns": list(prediction.columns), "rows": raw_rows.to_dict("records")}
