from datetime import date, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from app.models import PriceBar, Ticker
from app.main import app


def test_scanner_run_with_mock_data(monkeypatch, sample_bars):
    import app.services.scanner_engine as scanner_engine

    monkeypatch.setattr(scanner_engine, "fetch_daily_bars", lambda symbol, lookback_days=300: sample_bars)
    with TestClient(app) as client:
        response = client.post("/scan/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in ["completed", "partial_success"]
    assert payload["result_count"] > 0
    assert payload["results"][0]["score_total"] >= 0


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_journal_crud():
    with TestClient(app) as client:
        created = client.post(
            "/journal",
            json={
                "symbol": "AAPL",
                "setup_type": "Breakout Candidate",
                "direction": "long",
                "status": "closed",
                "planned_entry": 100,
                "actual_entry": 100,
                "exit_price": 110,
                "position_size": 2,
                "stop_loss": 95,
                "notes": "Test trade",
            },
        )

        assert created.status_code == 201
        entry = created.json()
        assert entry["pnl_amount"] == 20

        updated = client.patch(f"/journal/{entry['id']}", json={"lesson_learned": "Wait for confirmation"})
        assert updated.status_code == 200
        assert updated.json()["lesson_learned"] == "Wait for confirmation"

        deleted = client.delete(f"/journal/{entry['id']}")
        assert deleted.status_code == 204


def test_performance_summary_empty_or_valid():
    with TestClient(app) as client:
        response = client.get("/performance/summary")

    assert response.status_code == 200
    assert "total_trades" in response.json()


def test_price_data_backfills_chart_history(db_session, monkeypatch):
    import app.api.data as data_api

    ticker = Ticker(symbol="MU")
    db_session.add(ticker)
    db_session.commit()
    for index in range(60):
        close = 100 + index
        db_session.add(
            PriceBar(
                ticker_id=ticker.id,
                date=date.today() - timedelta(days=59 - index),
                open=close - 1,
                high=close + 1,
                low=close - 2,
                close=close,
                adjusted_close=close,
                volume=1_000_000,
            )
        )
    db_session.commit()

    start = date.today() - timedelta(days=520)
    backfilled = pd.DataFrame(
        [
            {
                "date": start + timedelta(days=index),
                "open": 50 + index,
                "high": 51 + index,
                "low": 49 + index,
                "close": 50 + index,
                "adjusted_close": 50 + index,
                "volume": 1_000_000 + index,
            }
            for index in range(420)
        ]
    )
    monkeypatch.setattr(data_api, "fetch_daily_bars", lambda symbol, lookback_days=800: backfilled)

    with TestClient(app) as client:
        response = client.get("/data/MU")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["date"] <= str(date.today() - timedelta(days=365))
    assert len(payload) >= 420
