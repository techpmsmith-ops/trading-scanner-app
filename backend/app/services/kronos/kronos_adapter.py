from datetime import datetime

import pandas as pd

from app.config import KRONOS_FORECAST_BARS, KRONOS_LOOKBACK_BARS
from app.services.kronos.kronos_schema import KronosBar, KronosForecastResult
from app.services.kronos.kronos_signal_mapper import confidence_from_move, direction_from_path

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]
STANDARD_HORIZONS = {
    "next_session": {"label": "Next Session", "bars": 1, "precision": "standard"},
    "three_trading_days": {"label": "3 Trading Days", "bars": 3, "precision": "standard"},
    "one_week": {"label": "1 Week", "bars": 5, "precision": "standard"},
    "one_month": {"label": "1 Month", "bars": 22, "precision": "medium"},
    "one_quarter": {"label": "1 Quarter", "bars": 65, "precision": "lower"},
}
DEFAULT_PRIMARY_HORIZON = "one_week"
MAX_STANDARD_HORIZON_BARS = max(item["bars"] for item in STANDARD_HORIZONS.values())


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
        standardized_horizons=_unavailable_horizons(error),
        horizon_summary=_horizon_summary(_unavailable_horizons(error)),
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
    horizons = _standardized_horizons(latest_close, prediction, model_name)
    primary = horizons.get(DEFAULT_PRIMARY_HORIZON) or {}
    return KronosForecastResult(
        symbol=symbol,
        timeframe=timeframe,
        forecast_horizon=int(primary.get("bars") or len(close_path)),
        predicted_direction=primary.get("direction") or direction,
        confidence_score=float(primary.get("confidence") if primary.get("confidence") is not None else confidence),
        predicted_close_path=close_path,
        predicted_high_low_range=primary.get("expected_range_values") or {"low": low, "high": high},
        volatility_estimate=volatility,
        model_name=model_name,
        lookback_bars_used=len(input_bars),
        created_at=datetime.utcnow(),
        raw_output=_prediction_raw_output(prediction),
        standardized_horizons=horizons,
        horizon_summary=_horizon_summary(horizons),
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


def _standardized_horizons(latest_close: float, prediction: pd.DataFrame, model_name: str) -> dict:
    horizons = {}
    close_path = [float(value) for value in prediction["close"].tolist()] if "close" in prediction else []
    for key, meta in STANDARD_HORIZONS.items():
        bars = min(int(meta["bars"]), len(close_path))
        if bars <= 0:
            horizons[key] = _unavailable_horizon("Forecast path is empty.", meta)
            continue
        window = prediction.iloc[:bars]
        closes = close_path[:bars]
        low = round(float(window["low"].min()), 4) if "low" in window and not window.empty else None
        high = round(float(window["high"].max()), 4) if "high" in window and not window.empty else None
        end_close = closes[-1]
        move_pct = ((end_close - latest_close) / latest_close) * 100 if latest_close else 0
        direction = direction_from_path(latest_close, closes)
        volatility = round(((max(closes) - min(closes)) / latest_close) * 100, 2) if latest_close and closes else None
        confidence = confidence_from_move(latest_close, closes, volatility)
        horizons[key] = {
            "label": meta["label"],
            "bars": bars,
            "bias": _bias_label(direction, key, volatility),
            "direction": direction,
            "confidence": confidence,
            "expected_range": _format_range(low, high),
            "expected_range_values": {"low": low, "high": high},
            "expected_move_pct": _format_move(move_pct),
            "expected_move_pct_value": round(move_pct, 2),
            "reason": _technical_reason(direction, key, move_pct, volatility, model_name),
            "risk": _technical_risk(direction, key, volatility),
            "trade_interpretation": _trade_interpretation(direction, key, confidence),
            "precision": meta["precision"],
        }
    return horizons


def _unavailable_horizons(error: str) -> dict:
    return {key: _unavailable_horizon(error, meta) for key, meta in STANDARD_HORIZONS.items()}


def _unavailable_horizon(error: str, meta: dict) -> dict:
    return {
        "label": meta["label"],
        "bars": meta["bars"],
        "bias": "unavailable",
        "direction": "unavailable",
        "confidence": 0,
        "expected_range": None,
        "expected_range_values": {"low": None, "high": None},
        "expected_move_pct": None,
        "expected_move_pct_value": None,
        "reason": "Kronos forecast is unavailable.",
        "risk": error,
        "trade_interpretation": "Do not use this horizon until Kronos produces a valid forecast.",
        "precision": meta["precision"],
    }


def _horizon_summary(horizons: dict) -> dict:
    highest_key = max(horizons, key=lambda key: float(horizons[key].get("confidence") or 0)) if horizons else None
    next_signal = horizons.get("next_session", {}).get("bias", "unavailable")
    week_signal = horizons.get("one_week", {}).get("bias", "unavailable")
    conflict = "None"
    if next_signal != "unavailable" and week_signal != "unavailable" and next_signal != week_signal:
        conflict = f"{next_signal} near-term signal inside a {week_signal} 1-week setup"
    return {
        "next_session_signal": next_signal,
        "three_day_signal": horizons.get("three_trading_days", {}).get("bias", "unavailable"),
        "one_week_signal": week_signal,
        "one_month_signal": horizons.get("one_month", {}).get("bias", "unavailable"),
        "one_quarter_signal": horizons.get("one_quarter", {}).get("bias", "unavailable"),
        "best_trading_horizon": _best_horizon(horizons),
        "highest_confidence_horizon": f"{horizons[highest_key]['label']}, {horizons[highest_key]['confidence']:.0f}%" if highest_key else "Unavailable",
        "timeframe_conflict": conflict,
        "suggested_action": _suggested_action(horizons),
    }


def _best_horizon(horizons: dict) -> str:
    preferred = ["one_week", "three_trading_days", "one_month", "next_session", "one_quarter"]
    for key in preferred:
        item = horizons.get(key) or {}
        if item.get("direction") in {"bullish", "bearish"} and float(item.get("confidence") or 0) >= 60:
            return f"{item['label']} {item['direction']} setup"
    return "Watchlist only until a higher-confidence horizon emerges"


def _suggested_action(horizons: dict) -> str:
    one_week = horizons.get("one_week", {})
    next_session = horizons.get("next_session", {})
    if one_week.get("direction") == "bullish" and next_session.get("direction") in {"neutral", "bearish"}:
        return "Wait for next-session confirmation, then consider swing entry if price holds support."
    if one_week.get("direction") == "bullish":
        return "Primary swing-trade window is 1 week; confirm support and volume before entry."
    if one_week.get("direction") == "bearish":
        return "Avoid new bullish entries until the 1-week signal stabilizes."
    return "Watchlist only; wait for clearer alignment across horizons."


def _bias_label(direction: str, key: str, volatility: float | None) -> str:
    suffix = " but volatile" if key in {"one_month", "one_quarter"} and volatility and volatility >= 5 else ""
    if direction == "bullish":
        return ("constructive long-term trend" if key == "one_quarter" else "bullish continuation") + suffix
    if direction == "bearish":
        return ("longer-term deterioration risk" if key == "one_quarter" else "bearish pressure") + suffix
    if direction == "neutral":
        return "neutral to slightly mixed" if key == "next_session" else "neutral consolidation"
    return "unavailable"


def _technical_reason(direction: str, key: str, move_pct: float, volatility: float | None, model_name: str) -> str:
    label = STANDARD_HORIZONS[key]["label"].lower()
    if direction == "bullish":
        return f"{model_name} forecast path shows upward pressure over the {label} window."
    if direction == "bearish":
        return f"{model_name} forecast path shows downside pressure over the {label} window."
    return f"{model_name} forecast path is not far enough from the latest close to indicate a directional edge."


def _technical_risk(direction: str, key: str, volatility: float | None) -> str:
    if volatility and volatility >= 5:
        return "Forecast band is wide, so position sizing and confirmation matter more."
    if direction == "bullish":
        return "Failure to hold short-term support would weaken the setup."
    if direction == "bearish":
        return "A strong close back above resistance could invalidate the bearish signal."
    return "Low directional edge can quickly flip if volume or market regime changes."


def _trade_interpretation(direction: str, key: str, confidence: float) -> str:
    if key == "next_session":
        return "Use for next-session risk context; wait for confirmation before acting."
    if key == "three_trading_days":
        return "Short swing candidate only if price confirms the forecast direction."
    if key == "one_week":
        return "Primary swing-trade window when confidence and technical setup align."
    if key == "one_month":
        return "Position-trade context; use wider stops and smaller size if volatility is elevated."
    return "Longer-term theme confirmation, not precise entry timing."


def _format_range(low: float | None, high: float | None) -> str | None:
    if low is None or high is None:
        return None
    return f"{low:.2f} - {high:.2f}"


def _format_move(move_pct: float) -> str:
    return f"{move_pct:+.2f}%"
