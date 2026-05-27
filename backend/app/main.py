import logging
from time import perf_counter

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, backtests, data, intelligence, journal, kronos, performance, phase2, research_portfolio, scanner, tickers
from app.config import ALLOWED_ORIGINS, APP_ENV, AUTO_CREATE_TABLES, DATABASE_URL, DEBUG, DEFAULT_UNIVERSE, FOCUS_GROUP_SYMBOLS, validate_runtime_config
from app.database import SessionLocal, init_db
from app.services.logging import log_event, log_exception
from app.services.intelligence import ensure_default_intelligence_watchlist
from app.services.phase2 import run_morning_phase2_pipeline
from app.services.scanner_engine import ScannerAlreadyRunning, ensure_default_universe, run_scanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Trading Scanner MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickers.router)
app.include_router(data.router)
app.include_router(scanner.router)
app.include_router(journal.router)
app.include_router(performance.router)
app.include_router(intelligence.router)
app.include_router(research_portfolio.router)
app.include_router(phase2.router)
app.include_router(backtests.router)
app.include_router(kronos.router)

scheduler = BackgroundScheduler(timezone="America/New_York")


@app.middleware("http")
async def request_timing_logger(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - started) * 1000, 2)
    log_event(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.on_event("startup")
def on_startup():
    validate_runtime_config()
    database_kind = "postgresql" if DATABASE_URL.startswith(("postgresql", "postgres")) else "sqlite"
    log_event(
        "startup_config",
        app_env=APP_ENV,
        debug=DEBUG,
        database=database_kind,
        auto_create_tables=AUTO_CREATE_TABLES,
        allowed_origins_count=len(ALLOWED_ORIGINS),
    )
    if AUTO_CREATE_TABLES:
        init_db()
    db = SessionLocal()
    try:
        ensure_default_universe(db, list(dict.fromkeys([*DEFAULT_UNIVERSE, *FOCUS_GROUP_SYMBOLS])))
        ensure_default_intelligence_watchlist(db)
    finally:
        db.close()
    if not scheduler.running:
        scheduler.add_job(scheduled_morning_pipeline, "cron", hour=7, minute=0, id="daily_premarket_pipeline", replace_existing=True)
        scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    return {"status": "ok", "service": "trading-scanner-api"}


def scheduled_scan():
    db = SessionLocal()
    try:
        run_scanner(db)
    except ScannerAlreadyRunning:
        log_event("scheduled_scan_skipped", reason="scanner_already_running")
    except Exception:
        log_exception("scheduled_scan_failed")
    finally:
        db.close()


def scheduled_morning_pipeline():
    db = SessionLocal()
    try:
        scan_run = run_scanner(db)
        if scan_run.status in {"completed", "partial_success"} and scan_run.result_count > 0:
            summary = run_morning_phase2_pipeline(db, scan_run)
            log_event("morning_phase2_pipeline_completed", **summary)
        else:
            log_event("morning_phase2_pipeline_skipped", scan_run_id=scan_run.id, status=scan_run.status)
    except ScannerAlreadyRunning:
        log_event("morning_phase2_pipeline_skipped", reason="scanner_already_running")
    except Exception:
        log_exception("morning_phase2_pipeline_failed")
    finally:
        db.close()
