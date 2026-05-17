from datetime import date
from pathlib import Path
import time

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.config import YFINANCE_CACHE_DIR
from app.models import PriceBar, Ticker
from app.services.logging import log_warning


def fetch_daily_bars(symbol: str, lookback_days: int = 300) -> pd.DataFrame:
    cache_dir = Path(YFINANCE_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir.resolve()))
    last_error: Exception | None = None
    data = pd.DataFrame()
    for attempt in range(1, 4):
        try:
            data = yf.download(
                symbol,
                period=f"{lookback_days}d",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=20,
            )
            if not data.empty:
                break
            last_error = ValueError(f"No market data returned for {symbol}")
        except Exception as exc:
            last_error = exc
        if attempt < 3:
            delay = attempt * 2
            log_warning("market_data_retry", symbol=symbol, attempt=attempt, delay_seconds=delay, error=str(last_error))
            time.sleep(delay)
    if data.empty:
        raise ValueError(f"No market data returned for {symbol}: {last_error}")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    data = data.reset_index()
    data.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adjusted_close",
            "Volume": "volume",
        },
        inplace=True,
    )
    return data[["date", "open", "high", "low", "close", "adjusted_close", "volume"]].dropna()


def upsert_price_bars(db: Session, ticker: Ticker, bars: pd.DataFrame) -> int:
    inserted = 0
    for row in bars.to_dict("records"):
        bar_date: date = pd.to_datetime(row["date"]).date()
        existing = (
            db.query(PriceBar)
            .filter(PriceBar.ticker_id == ticker.id, PriceBar.date == bar_date)
            .one_or_none()
        )
        values = {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "adjusted_close": float(row["adjusted_close"]),
            "volume": int(row["volume"]),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(PriceBar(ticker_id=ticker.id, date=bar_date, **values))
            inserted += 1
    db.commit()
    return inserted


def bars_for_ticker(db: Session, ticker: Ticker) -> pd.DataFrame:
    rows = db.query(PriceBar).filter(PriceBar.ticker_id == ticker.id).order_by(PriceBar.date.asc()).all()
    return pd.DataFrame(
        [
            {
                "date": row.date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "adjusted_close": row.adjusted_close,
                "volume": row.volume,
            }
            for row in rows
        ]
    )
