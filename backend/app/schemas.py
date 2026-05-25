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
    ticker_name: str | None = None
    ticker_description: str | None = None
    ticker_asset_type: str | None = None
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
    predicted_range_low: float | None
    predicted_range_high: float | None
    bullish_probability: float | None
    bearish_probability: float | None
    confidence: float
    score_total: int
    component_scores: dict[str, Any]
    key_drivers: list[str] | None = []
    main_risks: list[str] | None = []
    technical_setup: str | None
    sentiment_impact: str | None
    suggested_trade_plan: str | None
    rationale: str
    status: str
    start_price: float | None
    end_price: float | None
    actual_return_pct: float | None
    outcome: str | None
    outcome_reason: str | None
    range_hit: bool | None
    volume_confirmation: str | None
    sector_relative_behavior: str | None
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


class FocusGroupAnalysisRead(ORMModel):
    id: int
    analysis_date: date
    symbol: str
    scan_run_id: int | None
    scan_result_id: int | None
    bias: str
    confidence: float
    current_technical_setup: str
    key_catalyst: str
    risk_level: str
    suggested_watch_action: str
    entry_zone: str | None
    stop_loss_area: str | None
    target_zone: str | None
    daily_move_pct: float | None
    weekly_move_pct: float | None
    volume_spike: bool
    relative_volume: float | None
    indicators: dict[str, Any]
    support_resistance: dict[str, Any]
    catalysts: dict[str, Any]
    relevance: dict[str, Any]
    news_sentiment_score: float | None
    news_sentiment_label: str | None
    summary: str
    created_at: datetime


class FocusStockProfileRead(ORMModel):
    id: int
    symbol: str
    behavior_profile: dict[str, Any]
    indicator_weights: dict[str, Any]
    accuracy_stats: dict[str, Any]
    created_at: datetime
    updated_at: datetime


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
    focus_group: list[FocusGroupAnalysisRead]
    focus_profiles: list[FocusStockProfileRead]
    daily_top_five: list[DailyRecommendationRead]
    weekly_predictions: list[WeeklyPredictionRead]
    scoring_weights: ScoringWeightRead | None
    latest_evaluation: WeeklyEvaluationReportRead | None
    prediction_symbols: list[str]


class IntelligenceWatchlistCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    company_name: str | None = None
    priority: Literal["core", "high", "emerging", "monitor"] = "core"
    active: bool = True
    themes: list[str] = []
    thesis: str | None = None
    data_sources: list[str] = []
    notes: str | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class IntelligenceWatchlistUpdate(BaseModel):
    company_name: str | None = None
    priority: Literal["core", "high", "emerging", "monitor"] | None = None
    active: bool | None = None
    themes: list[str] | None = None
    thesis: str | None = None
    data_sources: list[str] | None = None
    notes: str | None = None


class IntelligenceWatchlistRead(IntelligenceWatchlistCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class IntelligenceModuleStatus(BaseModel):
    key: str
    name: str
    phase: int
    status: str
    responsibilities: list[str]
    data_sources: list[str]
    output_feeds: list[str]


class IntelligenceOpportunity(BaseModel):
    symbol: str
    bias: str
    conviction_score: float
    asymmetric_score: float
    momentum_score: float
    risk_score: float
    ai_relevance_score: float
    institutional_interest_score: float
    time_horizon: str
    catalysts: list[str]
    risks: list[str]
    action: str


class IntelligenceThemeTrend(BaseModel):
    theme: str
    strength: float
    symbol_count: int
    leaders: list[str]
    summary: str


class AgentScenarioResult(BaseModel):
    scenario: str
    probability: float
    expected_reaction: str
    vulnerable_symbols: list[str]
    likely_beneficiaries: list[str]
    confidence_adjustment: float
    risk_adjustment: float
    agent_consensus: dict[str, str]


class IntelligenceRiskOverview(BaseModel):
    regime: str
    portfolio_concentration: str
    crowded_trade_risk: str
    fragile_setups: list[str]
    notes: list[str]


class IntelligenceDashboard(BaseModel):
    generated_at: datetime
    mission: str
    modules: list[IntelligenceModuleStatus]
    watchlist: list[IntelligenceWatchlistRead]
    opportunities: list[IntelligenceOpportunity]
    theme_trends: list[IntelligenceThemeTrend]
    simulations: list[AgentScenarioResult]
    prediction_accuracy: dict[str, Any]
    risk_overview: IntelligenceRiskOverview
    next_actions: list[str]


class FocusExplainRequest(BaseModel):
    question: str | None = None


class FocusExplainResponse(BaseModel):
    symbol: str
    explanation: str
    disclaimer: str


class FocusExplanationContext(BaseModel):
    symbol: str
    latest_analysis: FocusGroupAnalysisRead | None
    weekly_predictions: list[WeeklyPredictionRead]
    profile: FocusStockProfileRead | None
    score_components: dict[str, Any]
    why_this_rating: dict[str, Any]
    recent_news_summary: dict[str, Any]
    disclaimer: str


class BacktestRunRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1, max_length=10)
    timeframe: Literal["daily", "weekly", "monthly"] = "daily"
    strategies: list[
        Literal[
            "trend_following",
            "momentum_strength",
            "breakout",
            "mean_reversion",
            "ai_composite",
        ]
    ] = ["trend_following", "momentum_strength", "breakout", "mean_reversion", "ai_composite"]
    lookback_days: int = Field(756, ge=120, le=2500)
    initial_capital: float = Field(10_000, gt=0, le=10_000_000)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, value: list[str]) -> list[str]:
        symbols = []
        for symbol in value:
            normalized = symbol.strip().upper()
            if normalized and normalized not in symbols:
                symbols.append(normalized)
        if not symbols:
            raise ValueError("At least one symbol is required")
        return symbols


class BacktestStrategyInfo(BaseModel):
    key: str
    name: str


class BacktestTrade(BaseModel):
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    result: str


class BacktestEquityPoint(BaseModel):
    date: str
    equity: float
    benchmark_equity: float


class BacktestMetrics(BaseModel):
    total_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    trade_count: int
    win_rate_pct: float
    average_trade_return_pct: float
    profit_factor: float | None
    final_equity: float


class BacktestResult(BaseModel):
    symbol: str
    strategy: str | None = None
    strategy_name: str | None = None
    timeframe: str | None = None
    metrics: BacktestMetrics | None = None
    trades: list[BacktestTrade] = []
    equity_curve: list[BacktestEquityPoint] = []
    notes: str | None = None
    error: str | None = None


class BacktestResponse(BaseModel):
    timeframe: str
    initial_capital: float
    symbols: list[str]
    strategies: list[str]
    results: list[BacktestResult]
    comparison: list[BacktestResult]
    disclaimer: str
