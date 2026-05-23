from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TickerBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    name: str | None = None
    asset_type: str = "stock"
    active: bool = True

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class TickerCreate(TickerBase):
    pass


class TickerUpdate(BaseModel):
    name: str | None = None
    asset_type: str | None = None
    active: bool | None = None


class TickerRead(TickerBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class PriceBarRead(ORMModel):
    id: int
    ticker_id: int
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


class ScanResultRead(ORMModel):
    id: int
    scan_run_id: int
    ticker_id: int
    symbol: str
    close_price: float
    score_total: int
    score_trend: int
    score_momentum: int
    score_volume: int
    score_risk: int
    score_setup_quality: int
    setup_types: list[str]
    risk_flags: list[str]
    indicators: dict[str, Any]
    entry_zone: float | None
    stop_loss: float | None
    target_1: float | None
    target_2: float | None
    risk_reward: float | None
    explanation: str
    created_at: datetime


class ScanRunRead(ORMModel):
    id: int
    run_date: date
    status: str
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    universe_count: int
    result_count: int
    duration_seconds: float | None


class ScanRunDetail(ScanRunRead):
    results: list[ScanResultRead] = []


class ScanStatus(ORMModel):
    latest_run: ScanRunRead | None = None
    last_successful_scan: ScanRunRead | None = None
    running: bool = False


class JournalBase(BaseModel):
    symbol: str
    setup_type: str = "manual"
    direction: Literal["long", "short", "watchlist"] = "watchlist"
    status: Literal["planned", "open", "closed", "skipped"] = "planned"
    planned_entry: float | None = None
    actual_entry: float | None = None
    stop_loss: float | None = None
    target_1: float | None = None
    target_2: float | None = None
    exit_price: float | None = None
    position_size: float | None = None
    risk_amount: float | None = None
    entry_date: date | None = None
    exit_date: date | None = None
    pnl_amount: float | None = None
    pnl_percent: float | None = None
    result: Literal["win", "loss", "breakeven", "skipped"] | None = None
    notes: str | None = None
    emotions: str | None = None
    mistake_tags: list[str] | None = None
    lesson_learned: str | None = None
    linked_scan_result_id: int | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class JournalCreate(JournalBase):
    pass


class JournalUpdate(BaseModel):
    symbol: str | None = None
    setup_type: str | None = None
    direction: Literal["long", "short", "watchlist"] | None = None
    status: Literal["planned", "open", "closed", "skipped"] | None = None
    planned_entry: float | None = None
    actual_entry: float | None = None
    stop_loss: float | None = None
    target_1: float | None = None
    target_2: float | None = None
    exit_price: float | None = None
    position_size: float | None = None
    risk_amount: float | None = None
    entry_date: date | None = None
    exit_date: date | None = None
    pnl_amount: float | None = None
    pnl_percent: float | None = None
    result: Literal["win", "loss", "breakeven", "skipped"] | None = None
    notes: str | None = None
    emotions: str | None = None
    mistake_tags: list[str] | None = None
    lesson_learned: str | None = None
    linked_scan_result_id: int | None = None


class JournalRead(JournalBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class PerformanceSummary(BaseModel):
    total_trades: int
    wins: int
    losses: int
    breakeven_trades: int
    win_rate: float
    average_gain: float
    average_loss: float
    total_pnl: float
    best_trade: float | None
    worst_trade: float | None
    most_common_mistake_tags: list[dict[str, Any]]


class UserRead(ORMModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class DailyRecommendationRead(ORMModel):
    id: int
    recommendation_date: date
    scan_run_id: int
    scan_result_id: int
    symbol: str
    rank: int
    score_total: int
    setup_types: list[str]
    risk_flags: list[str]
    rationale: str
    disclaimer: str
    created_at: datetime


class WeeklyPredictionRead(ORMModel):
    id: int
    week_start: date
    week_end: date
    symbol: str
    scan_run_id: int | None
    scan_result_id: int | None
    direction: str
    predicted_return_pct: float
    confidence: float
    score_total: int
    component_scores: dict[str, Any]
    rationale: str
    status: str
    start_price: float | None
    end_price: float | None
    actual_return_pct: float | None
    outcome: str | None
    false_positive: bool
    news_sentiment_score: float | None
    news_sentiment_label: str | None
    created_at: datetime
    evaluated_at: datetime | None


class ScoringWeightRead(ORMModel):
    id: int
    effective_date: date
    weights: dict[str, float]
    reason: str
    created_at: datetime


class WeeklyEvaluationReportRead(ORMModel):
    id: int
    week_start: date
    week_end: date
    evaluated_count: int
    accuracy: float
    wins: int
    losses: int
    win_loss_ratio: float | None
    false_positives: int
    indicator_effectiveness: dict[str, Any]
    news_sentiment_correlation: dict[str, Any]
    market_conditions: dict[str, Any]
    weight_changes: dict[str, Any]
    confidence_notes: str
    created_at: datetime


class AlertSubscriptionCreate(BaseModel):
    channel: Literal["telegram", "sms"]
    destination_label: str | None = None
    enabled: bool = True
    alert_types: list[str] = ["daily_top_five", "weekly_predictions"]


class AlertSubscriptionUpdate(BaseModel):
    destination_label: str | None = None
    enabled: bool | None = None
    alert_types: list[str] | None = None


class AlertSubscriptionRead(AlertSubscriptionCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class AlertTestResponse(BaseModel):
    channel: str
    configured: bool
    sent: bool
    detail: str


class Phase2Dashboard(BaseModel):
    daily_top_five: list[DailyRecommendationRead]
    weekly_predictions: list[WeeklyPredictionRead]
    scoring_weights: ScoringWeightRead | None
    latest_evaluation: WeeklyEvaluationReportRead | None
    prediction_symbols: list[str]
