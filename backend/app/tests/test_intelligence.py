from datetime import date

from app.models import FocusGroupAnalysis, IntelligenceWatchlistSymbol, ScanResult, ScanRun, Ticker
from app.services.intelligence import intelligence_dashboard, list_watchlist, upsert_watchlist_symbol


def test_intelligence_watchlist_seeds_initial_focus_group(db_session):
    rows = list_watchlist(db_session)

    symbols = {row.symbol for row in rows}
    assert {"INTC", "NVDA", "AMD", "IONQ", "NVTS", "RVI", "SMCI", "RGTI", "RKLB", "MU"}.issubset(symbols)
    assert all(row.active for row in rows)
    assert any("AI accelerators" in row.themes for row in rows if row.symbol == "NVDA")


def test_intelligence_watchlist_allows_dynamic_expansion(db_session):
    row = upsert_watchlist_symbol(
        db_session,
        {
            "symbol": "AVGO",
            "company_name": "Broadcom",
            "priority": "high",
            "active": True,
            "themes": ["AI networking", "custom silicon", "semiconductors"],
            "thesis": "AI networking and custom silicon expansion candidate.",
            "data_sources": ["SEC filings", "News APIs"],
            "notes": "Added from broader discovery.",
        },
    )

    assert row.symbol == "AVGO"
    assert db_session.query(IntelligenceWatchlistSymbol).filter(IntelligenceWatchlistSymbol.symbol == "AVGO").one()


def test_intelligence_dashboard_combines_focus_scanner_and_simulation(db_session):
    ticker = Ticker(symbol="NVDA")
    run = ScanRun(run_date=date.today(), status="completed", universe_count=1, result_count=1)
    db_session.add_all([ticker, run])
    db_session.commit()
    result = ScanResult(
        scan_run_id=run.id,
        ticker_id=ticker.id,
        symbol="NVDA",
        close_price=900,
        score_total=88,
        score_trend=28,
        score_momentum=19,
        score_volume=15,
        score_risk=14,
        score_setup_quality=12,
        setup_types=["Momentum Strength"],
        risk_flags=[],
        indicators={"atr_percent": 3.2},
        explanation="Test",
    )
    focus = FocusGroupAnalysis(
        analysis_date=date.today(),
        symbol="NVDA",
        scan_run_id=run.id,
        scan_result_id=None,
        bias="bullish",
        confidence=0.72,
        current_technical_setup="Momentum Strength",
        key_catalyst="AI data-center capex acceleration.",
        risk_level="medium",
        suggested_watch_action="Watch for confirmation.",
        volume_spike=True,
        relative_volume=1.8,
        indicators={},
        support_resistance={},
        catalysts={},
        relevance={"tags": ["AI infrastructure"]},
        summary="NVDA focus view is bullish.",
    )
    db_session.add_all([result, focus])
    db_session.commit()

    dashboard = intelligence_dashboard(db_session)

    nvda = next(item for item in dashboard["opportunities"] if item["symbol"] == "NVDA")
    assert nvda["conviction_score"] > 60
    assert dashboard["modules"]
    assert dashboard["simulations"]
    assert dashboard["risk_overview"]["regime"] in {"risk-on", "selective", "defensive"}
