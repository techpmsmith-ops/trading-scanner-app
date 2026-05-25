from fastapi.testclient import TestClient

from app.main import app


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
