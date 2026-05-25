from datetime import date, datetime
from threading import Lock
from time import perf_counter

from sqlalchemy.orm import Session

from app.config import DEFAULT_TICKER_METADATA, SCAN_DEFAULT_LOOKBACK_DAYS
from app.models import ScanResult, ScanRun, Ticker
from app.services.explanations import build_explanation
from app.services.indicators import latest_indicator_snapshot
from app.services.market_data import bars_for_ticker, fetch_daily_bars, upsert_price_bars
from app.services.logging import log_event, log_warning
from app.services.phase2 import latest_weights
from app.services.risk_reward import estimate_risk_reward
from app.services.scoring import classify_setups, score_result

_scan_lock = Lock()


class ScannerAlreadyRunning(Exception):
    pass


def ensure_default_universe(db: Session, symbols: list[str]) -> None:
    for symbol in symbols:
        normalized = symbol.strip().upper()
        metadata = DEFAULT_TICKER_METADATA.get(normalized, {})
        ticker = db.query(Ticker).filter(Ticker.symbol == normalized).one_or_none()
        if not ticker:
            db.add(
                Ticker(
                    symbol=normalized,
                    name=metadata.get("name"),
                    asset_type=metadata.get("asset_type", "stock"),
                )
            )
        else:
            if not ticker.name and metadata.get("name"):
                ticker.name = metadata["name"]
            if ticker.asset_type == "stock" and metadata.get("asset_type"):
                ticker.asset_type = metadata["asset_type"]
    db.commit()


def run_scanner(db: Session, lookback_days: int = SCAN_DEFAULT_LOOKBACK_DAYS) -> ScanRun:
    if not _scan_lock.acquire(blocking=False):
        raise ScannerAlreadyRunning("A scanner run is already in progress")
    started = perf_counter()
    try:
        tickers = db.query(Ticker).filter(Ticker.active.is_(True)).order_by(Ticker.symbol.asc()).all()
        scan_run = ScanRun(run_date=date.today(), status="running", universe_count=len(tickers), result_count=0)
        db.add(scan_run)
        db.commit()
        db.refresh(scan_run)
        log_event("scan_started", scan_run_id=scan_run.id, universe_count=len(tickers))

        failures: list[str] = []
        results_count = 0
        component_weights = latest_weights(db)
        for ticker in tickers:
            try:
                downloaded = fetch_daily_bars(ticker.symbol, lookback_days=lookback_days)
                upsert_price_bars(db, ticker, downloaded)
                bars = bars_for_ticker(db, ticker)
                if len(bars) < 220:
                    raise ValueError("Not enough daily bars for reliable long-term indicators")

                indicators = latest_indicator_snapshot(bars)
                setups, risk_flags = classify_setups(indicators)
                scores = score_result(indicators, setups, risk_flags, component_weights=component_weights)
                rr = estimate_risk_reward(indicators, setups)
                explanation = build_explanation(ticker.symbol, scores, indicators, setups, risk_flags)
                db.add(
                    ScanResult(
                        scan_run_id=scan_run.id,
                        ticker_id=ticker.id,
                        symbol=ticker.symbol,
                        close_price=indicators["close"],
                        setup_types=setups,
                        risk_flags=risk_flags,
                        indicators=indicators,
                        explanation=explanation,
                        **scores,
                        **rr,
                    )
                )
                results_count += 1
                db.commit()
            except Exception as exc:
                db.rollback()
                failures.append(f"{ticker.symbol}: {exc}")
                log_warning("scan_ticker_failed", scan_run_id=scan_run.id, symbol=ticker.symbol, error=str(exc))

        scan_run.completed_at = datetime.utcnow()
        scan_run.result_count = results_count
        scan_run.duration_seconds = round(perf_counter() - started, 3)
        if failures and results_count:
            scan_run.status = "partial_success"
            scan_run.error_message = "\n".join(failures)
        elif failures:
            scan_run.status = "failed"
            scan_run.error_message = "\n".join(failures)
        else:
            scan_run.status = "completed"
        db.commit()
        db.refresh(scan_run)
        log_event(
            "scan_completed",
            scan_run_id=scan_run.id,
            status=scan_run.status,
            result_count=scan_run.result_count,
            universe_count=scan_run.universe_count,
            duration_seconds=scan_run.duration_seconds,
        )
        return scan_run
    finally:
        _scan_lock.release()
