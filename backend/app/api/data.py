from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import SCAN_DEFAULT_LOOKBACK_DAYS
from app.database import get_db
from app.models import PriceBar, Ticker
from app.schemas import PriceBarRead
from app.services.auth import get_current_user
from app.services.market_data import fetch_daily_bars, upsert_price_bars

router = APIRouter(prefix="/data", tags=["market data"], dependencies=[Depends(get_current_user)])

CHART_LOOKBACK_DAYS = 800
MIN_CHART_HISTORY_DAYS = 370


@router.post("/refresh")
def refresh_data(db: Session = Depends(get_db)):
    tickers = db.query(Ticker).filter(Ticker.active.is_(True)).all()
    failures = []
    refreshed = 0
    for ticker in tickers:
        try:
            bars = fetch_daily_bars(ticker.symbol, SCAN_DEFAULT_LOOKBACK_DAYS)
            upsert_price_bars(db, ticker, bars)
            refreshed += 1
        except Exception as exc:
            failures.append({"symbol": ticker.symbol, "error": str(exc)})
    return {"refreshed": refreshed, "failed": failures, "universe_count": len(tickers)}


@router.get("/{symbol}", response_model=list[PriceBarRead])
def get_data(symbol: str, db: Session = Depends(get_db)):
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol.upper()).one_or_none()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    ensure_chart_history(db, ticker)
    return (
        db.query(PriceBar)
        .filter(PriceBar.ticker_id == ticker.id)
        .order_by(PriceBar.date.asc())
        .all()
    )


def ensure_chart_history(db: Session, ticker: Ticker) -> None:
    oldest = db.query(PriceBar).filter(PriceBar.ticker_id == ticker.id).order_by(PriceBar.date.asc()).first()
    latest = db.query(PriceBar).filter(PriceBar.ticker_id == ticker.id).order_by(PriceBar.date.desc()).first()
    today = date.today()
    has_enough_history = oldest and oldest.date <= today - timedelta(days=MIN_CHART_HISTORY_DAYS)
    has_recent_bar = latest and latest.date >= today - timedelta(days=7)
    if has_enough_history and has_recent_bar:
        return
    try:
        bars = fetch_daily_bars(ticker.symbol, CHART_LOOKBACK_DAYS)
        upsert_price_bars(db, ticker, bars)
    except Exception:
        if not latest:
            raise
