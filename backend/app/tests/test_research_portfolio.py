from fastapi.testclient import TestClient

from app.main import app
from app.models import ResearchPosition, Ticker


def test_research_portfolio_tracks_shares_and_leaps(db_session):
    with TestClient(app) as client:
        shares = client.post(
            "/research-portfolio/positions",
            json={
                "symbol": "NVDA",
                "position_type": "shares",
                "role": "core",
                "theme": "AI accelerators",
                "thesis": "AI infrastructure leader.",
                "conviction": "high",
                "quantity": 10,
                "average_cost": 100,
                "current_price": 125,
            },
        )
        leaps = client.post(
            "/research-portfolio/positions",
            json={
                "symbol": "MU",
                "position_type": "leaps",
                "role": "growth",
                "theme": "HBM memory",
                "thesis": "Memory bandwidth demand tied to AI infrastructure.",
                "conviction": "high",
                "contracts": 2,
                "strike_price": 90,
                "premium_paid": 12,
                "current_contract_price": 18,
            },
        )
        dashboard = client.get("/research-portfolio")

    assert shares.status_code == 201
    assert shares.json()["market_value"] == 1250
    assert leaps.status_code == 201
    assert leaps.json()["break_even"] == 102
    assert leaps.json()["market_value"] == 3600
    payload = dashboard.json()
    assert payload["summary"]["current_value"] == 4850
    assert payload["summary"]["leaps_exposure_pct"] > 70
    assert payload["summary"]["goals"][0]["target_value"] == 250000
    assert len(payload["positions"]) == 2


def test_research_position_adds_symbol_to_scanner_universe(db_session):
    with TestClient(app) as client:
        response = client.post(
            "/research-portfolio/positions",
            json={
                "symbol": "TSM",
                "position_type": "shares",
                "role": "growth",
                "theme": "AI foundry",
                "conviction": "high",
                "quantity": 5,
                "average_cost": 120,
                "current_price": 130,
            },
        )

    assert response.status_code == 201
    ticker = db_session.query(Ticker).filter(Ticker.symbol == "TSM").one()
    assert ticker.active is True


def test_scanner_updates_research_share_price(db_session, monkeypatch, sample_bars):
    import app.services.scanner_engine as scanner_engine

    db_session.add(Ticker(symbol="NVDA", active=True))
    db_session.add(
        ResearchPosition(
            symbol="NVDA",
            position_type="shares",
            role="core",
            theme="AI accelerators",
            conviction="high",
            quantity=10,
            average_cost=100,
            current_price=100,
        )
    )
    db_session.commit()
    sample_bars.loc[sample_bars.index[-1], "close"] = 175
    sample_bars.loc[sample_bars.index[-1], "adjusted_close"] = 175
    monkeypatch.setattr(scanner_engine, "fetch_daily_bars", lambda symbol, lookback_days=300: sample_bars)

    with TestClient(app) as client:
        response = client.post("/scan/run")

    assert response.status_code == 200
    position = db_session.query(ResearchPosition).filter(ResearchPosition.symbol == "NVDA").one()
    assert position.current_price == 175
