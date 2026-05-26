from datetime import date, timedelta

import pandas as pd
import pytest

from app.main import app
from app.database import Base, SessionLocal, engine, init_db
from app.models import AlertSubscription, DailyRecommendation, FocusGroupAnalysis, FocusStockProfile, IntelligenceWatchlistSymbol, KronosPredictionEvaluation, PriceBar, ResearchPosition, ScanResult, ScanRun, ScoringWeight, Ticker, User, WeeklyEvaluationReport, WeeklyPrediction
from app.services.auth import get_current_user


@pytest.fixture(autouse=True)
def authenticated_test_user():
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        email="test@example.com",
        hashed_password="unused",
        is_active=True,
        is_admin=True,
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def sample_bars(days: int = 260) -> pd.DataFrame:
    start = date.today() - timedelta(days=days * 2)
    rows = []
    price = 100.0
    for index in range(days):
        price += 0.25
        current = start + timedelta(days=index)
        rows.append(
            {
                "date": current,
                "open": price - 0.5,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "adjusted_close": price,
                "volume": 1_000_000 + index * 1000,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    for model in [ResearchPosition, KronosPredictionEvaluation, DailyRecommendation, WeeklyEvaluationReport, WeeklyPrediction, FocusGroupAnalysis, FocusStockProfile, IntelligenceWatchlistSymbol, ScoringWeight, AlertSubscription, ScanResult, PriceBar, ScanRun, Ticker]:
        db.query(model).delete()
    db.commit()
    try:
        yield db
    finally:
        db.rollback()
        for model in [ResearchPosition, KronosPredictionEvaluation, DailyRecommendation, WeeklyEvaluationReport, WeeklyPrediction, FocusGroupAnalysis, FocusStockProfile, IntelligenceWatchlistSymbol, ScoringWeight, AlertSubscription, ScanResult, PriceBar, ScanRun, Ticker]:
            db.query(model).delete()
        db.commit()
        db.close()
