from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DEFAULT_TICKER_METADATA
from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Ticker(Base, TimestampMixin):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(32), default="stock")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    price_bars = relationship("PriceBar", back_populates="ticker", cascade="all, delete-orphan")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class PriceBar(Base):
    __tablename__ = "price_bars"
    __table_args__ = (UniqueConstraint("ticker_id", "date", name="uq_price_bars_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adjusted_close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticker = relationship("Ticker", back_populates="price_bars")


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    universe_count: Mapped[int] = mapped_column(Integer, default=0)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    results = relationship("ScanResult", back_populates="scan_run", cascade="all, delete-orphan")


class ScanResult(Base):
    __tablename__ = "scan_results"
    __table_args__ = (UniqueConstraint("scan_run_id", "ticker_id", name="uq_scan_results_run_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id"), index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    close_price: Mapped[float] = mapped_column(Float)
    score_total: Mapped[int] = mapped_column(Integer)
    score_trend: Mapped[int] = mapped_column(Integer)
    score_momentum: Mapped[int] = mapped_column(Integer)
    score_volume: Mapped[int] = mapped_column(Integer)
    score_risk: Mapped[int] = mapped_column(Integer)
    score_setup_quality: Mapped[int] = mapped_column(Integer)
    setup_types: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    indicators: Mapped[dict] = mapped_column(JSON, default=dict)
    entry_zone: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan_run = relationship("ScanRun", back_populates="results")
    ticker = relationship("Ticker")

    @property
    def ticker_name(self) -> str | None:
        metadata = DEFAULT_TICKER_METADATA.get(self.symbol.upper(), {})
        return self.ticker.name if self.ticker and self.ticker.name else metadata.get("name")

    @property
    def ticker_description(self) -> str | None:
        metadata = DEFAULT_TICKER_METADATA.get(self.symbol.upper(), {})
        return metadata.get("description") or self.ticker_name

    @property
    def ticker_asset_type(self) -> str | None:
        metadata = DEFAULT_TICKER_METADATA.get(self.symbol.upper(), {})
        return self.ticker.asset_type if self.ticker else metadata.get("asset_type")


class DailyRecommendation(Base):
    __tablename__ = "daily_recommendations"
    __table_args__ = (UniqueConstraint("recommendation_date", "rank", name="uq_daily_recommendations_date_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_date: Mapped[date] = mapped_column(Date, index=True)
    scan_run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id"), index=True)
    scan_result_id: Mapped[int] = mapped_column(ForeignKey("scan_results.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    score_total: Mapped[int] = mapped_column(Integer)
    setup_types: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan_result = relationship("ScanResult")
    scan_run = relationship("ScanRun")


class WeeklyPrediction(Base):
    __tablename__ = "weekly_predictions"
    __table_args__ = (UniqueConstraint("week_start", "symbol", name="uq_weekly_predictions_week_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    scan_run_id: Mapped[int | None] = mapped_column(ForeignKey("scan_runs.id"), nullable=True)
    scan_result_id: Mapped[int | None] = mapped_column(ForeignKey("scan_results.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20))
    predicted_return_pct: Mapped[float] = mapped_column(Float)
    predicted_range_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_range_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    bullish_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    bearish_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    score_total: Mapped[int] = mapped_column(Integer, default=0)
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    key_drivers: Mapped[list] = mapped_column(JSON, default=list)
    main_risks: Mapped[list] = mapped_column(JSON, default=list)
    technical_setup: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_trade_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    start_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    outcome_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    range_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    volume_confirmation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sector_relative_behavior: Mapped[str | None] = mapped_column(String(80), nullable=True)
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    news_sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    news_sentiment_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    scan_result = relationship("ScanResult")
    scan_run = relationship("ScanRun")


class FocusGroupAnalysis(Base):
    __tablename__ = "focus_group_analyses"
    __table_args__ = (UniqueConstraint("analysis_date", "symbol", name="uq_focus_group_analyses_date_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_date: Mapped[date] = mapped_column(Date, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    scan_run_id: Mapped[int | None] = mapped_column(ForeignKey("scan_runs.id"), nullable=True)
    scan_result_id: Mapped[int | None] = mapped_column(ForeignKey("scan_results.id"), nullable=True)
    bias: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    current_technical_setup: Mapped[str] = mapped_column(Text)
    key_catalyst: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(20))
    suggested_watch_action: Mapped[str] = mapped_column(Text)
    entry_zone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stop_loss_area: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_zone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    daily_move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    weekly_move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_spike: Mapped[bool] = mapped_column(Boolean, default=False)
    relative_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    indicators: Mapped[dict] = mapped_column(JSON, default=dict)
    support_resistance: Mapped[dict] = mapped_column(JSON, default=dict)
    catalysts: Mapped[dict] = mapped_column(JSON, default=dict)
    relevance: Mapped[dict] = mapped_column(JSON, default=dict)
    news_sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    news_sentiment_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan_result = relationship("ScanResult")
    scan_run = relationship("ScanRun")


class FocusStockProfile(Base, TimestampMixin):
    __tablename__ = "focus_stock_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    behavior_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    indicator_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    accuracy_stats: Mapped[dict] = mapped_column(JSON, default=dict)


class IntelligenceWatchlistSymbol(Base, TimestampMixin):
    __tablename__ = "intelligence_watchlist_symbols"
    __table_args__ = (UniqueConstraint("symbol", name="uq_intelligence_watchlist_symbols_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="core")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_sources: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScoringWeight(Base):
    __tablename__ = "scoring_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    effective_date: Mapped[date] = mapped_column(Date, index=True)
    weights: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WeeklyEvaluationReport(Base):
    __tablename__ = "weekly_evaluation_reports"
    __table_args__ = (UniqueConstraint("week_start", "week_end", name="uq_weekly_evaluation_reports_week"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date, index=True)
    evaluated_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    win_loss_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    false_positives: Mapped[int] = mapped_column(Integer, default=0)
    indicator_effectiveness: Mapped[dict] = mapped_column(JSON, default=dict)
    news_sentiment_correlation: Mapped[dict] = mapped_column(JSON, default=dict)
    market_conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    weight_changes: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AlertSubscription(Base, TimestampMixin):
    __tablename__ = "alert_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    destination_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_types: Mapped[list] = mapped_column(JSON, default=list)


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    setup_type: Mapped[str] = mapped_column(String(80))
    direction: Mapped[str] = mapped_column(String(20), default="watchlist")
    status: Mapped[str] = mapped_column(String(20), default="planned")
    planned_entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pnl_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotions: Mapped[str | None] = mapped_column(Text, nullable=True)
    mistake_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    lesson_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_scan_result_id: Mapped[int | None] = mapped_column(ForeignKey("scan_results.id"), nullable=True)
