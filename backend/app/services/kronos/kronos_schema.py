from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


KronosDirection = Literal["bullish", "bearish", "neutral", "unavailable"]


class KronosBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float | None = None


class KronosForecastRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    bars: list[KronosBar] = Field(default_factory=list)
    forecast_bars: int | None = None
    fetch_from_polygon: bool = False


class KronosForecastResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    symbol: str
    timeframe: str
    forecast_horizon: int
    predicted_direction: KronosDirection
    confidence_score: float
    predicted_close_path: list[float] = Field(default_factory=list)
    predicted_high_low_range: dict[str, float | None] = Field(default_factory=dict)
    volatility_estimate: float | None = None
    model_name: str
    lookback_bars_used: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    raw_output: dict[str, Any] = Field(default_factory=dict)


class KronosSignal(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    kronos_bias: KronosDirection
    kronos_confidence: float
    kronos_expected_range: dict[str, float | None] = Field(default_factory=dict)
    kronos_risk_flag: str | None = None
    kronos_summary: str
    forecast: KronosForecastResult
