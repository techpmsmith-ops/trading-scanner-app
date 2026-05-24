from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BacktestResponse, BacktestRunRequest, BacktestStrategyInfo
from app.services.auth import get_current_user
from app.services.backtesting import STRATEGY_NAMES, BacktestRequest, run_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"], dependencies=[Depends(get_current_user)])


@router.get("/strategies", response_model=list[BacktestStrategyInfo])
def strategies():
    return [{"key": key, "name": name} for key, name in STRATEGY_NAMES.items()]


@router.post("/run", response_model=BacktestResponse)
def run_backtest_endpoint(payload: BacktestRunRequest, db: Session = Depends(get_db)):
    try:
        return run_backtest(
            db,
            BacktestRequest(
                symbols=payload.symbols,
                timeframe=payload.timeframe,
                strategies=payload.strategies,
                lookback_days=payload.lookback_days,
                initial_capital=payload.initial_capital,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
