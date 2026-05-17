from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import ScanResult, ScanRun
from app.schemas import ScanResultRead, ScanRunDetail, ScanRunRead, ScanStatus
from app.services.auth import get_current_admin, get_current_user
from app.services.scanner_engine import ScannerAlreadyRunning, run_scanner

router = APIRouter(prefix="/scan", tags=["scanner"], dependencies=[Depends(get_current_user)])


@router.post("/run", response_model=ScanRunDetail)
def run_scan(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    try:
        scan_run = run_scanner(db)
    except ScannerAlreadyRunning as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return (
        db.query(ScanRun)
        .options(selectinload(ScanRun.results))
        .filter(ScanRun.id == scan_run.id)
        .one()
    )


@router.get("/runs", response_model=list[ScanRunRead])
def list_runs(db: Session = Depends(get_db)):
    return db.query(ScanRun).order_by(ScanRun.started_at.desc()).limit(50).all()


@router.get("/status", response_model=ScanStatus)
def scan_status(db: Session = Depends(get_db)):
    latest_run = db.query(ScanRun).order_by(ScanRun.started_at.desc()).first()
    last_successful_scan = (
        db.query(ScanRun)
        .filter(ScanRun.status.in_(["completed", "partial_success"]), ScanRun.result_count > 0)
        .order_by(ScanRun.completed_at.desc())
        .first()
    )
    running = db.query(ScanRun).filter(ScanRun.status == "running").first() is not None
    return {"latest_run": latest_run, "last_successful_scan": last_successful_scan, "running": running}


@router.get("/runs/{run_id}", response_model=ScanRunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)):
    scan_run = (
        db.query(ScanRun)
        .options(selectinload(ScanRun.results))
        .filter(ScanRun.id == run_id)
        .one_or_none()
    )
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan run not found")
    scan_run.results.sort(key=lambda item: item.score_total, reverse=True)
    return scan_run


@router.get("/latest", response_model=ScanRunDetail)
def latest_scan(db: Session = Depends(get_db)):
    scan_run = (
        db.query(ScanRun)
        .options(selectinload(ScanRun.results))
        .order_by(ScanRun.started_at.desc())
        .first()
    )
    if not scan_run:
        raise HTTPException(status_code=404, detail="No scan results found")
    scan_run.results.sort(key=lambda item: item.score_total, reverse=True)
    return scan_run


@router.get("/results/{result_id}", response_model=ScanResultRead)
def get_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(ScanResult).filter(ScanResult.id == result_id).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result
