from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models import PriceBar, Ticker
from app.services.backtesting import BacktestRequest, run_backtest


def seed_bars(db_session, symbol: str = "TEST", days: int = 260) -> None:
    ticker = Ticker(symbol=symbol, active=True)
    db_session.add(ticker)
    db_session.flush()
    start = date.today() - timedelta(days=days)
    price = 100.0
    for index in range(days):
        price += 0.22 if index % 17 else -0.65
        db_session.add(
            PriceBar(
                ticker_id=ticker.id,
                date=start + timedelta(days=index),
                open=price - 0.4,
                high=price + 0.9,
                low=price - 0.9,
                close=price,
                adjusted_close=price,
                volume=1_000_000 + index * 1000,
            )
        )
    db_session.commit()


def test_backtest_engine_returns_risk_adjusted_metrics(db_session):
    seed_bars(db_session)

    report = run_backtest(
        db_session,
        BacktestRequest(
            symbols=["TEST"],
            timeframe="daily",
            strategies=["trend_following", "ai_composite"],
            lookback_days=260,
            initial_capital=10_000,
        ),
    )

    assert report["timeframe"] == "daily"
    assert len(report["results"]) == 2
    metrics = report["results"][0]["metrics"]
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert "win_rate_pct" in metrics
    assert report["comparison"]


def test_backtest_engine_supports_weekly_timeframe(db_session):
    seed_bars(db_session, symbol="WEEK", days=420)

    report = run_backtest(
        db_session,
        BacktestRequest(symbols=["WEEK"], timeframe="weekly", strategies=["ai_composite"], lookback_days=420),
    )

    result = report["results"][0]
    assert result["timeframe"] == "weekly"
    assert result["equity_curve"]


def test_backtest_api_endpoint(db_session):
    seed_bars(db_session, symbol="API", days=260)
    client = TestClient(app)

    response = client.post(
        "/backtests/run",
        json={
            "symbols": ["API"],
            "timeframe": "daily",
            "strategies": ["momentum_strength"],
            "lookback_days": 260,
            "initial_capital": 5000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbols"] == ["API"]
    assert body["results"][0]["metrics"]["final_equity"] > 0
