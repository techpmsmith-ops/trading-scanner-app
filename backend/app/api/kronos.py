import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.config import KRONOS_ENABLED, KRONOS_FORECAST_BARS, KRONOS_MODEL_NAME, KRONOS_TOKENIZER_NAME
from app.schemas import KronosForecastApiRequest, KronosHealthRead
from app.services.auth import get_current_admin, get_current_user
from app.services.kronos.kronos_adapter import dataframe_to_kronos_bars
from app.services.kronos.kronos_client import get_kronos_client
from app.services.kronos.service import forecast_signal
from app.services.market_data import fetch_polygon_daily_bars

router = APIRouter(prefix="/api/kronos", tags=["kronos"], dependencies=[Depends(get_current_user)])


@router.get("/health", response_model=KronosHealthRead)
def kronos_health():
    client = get_kronos_client()
    health = client.health()
    return {
        "enabled": KRONOS_ENABLED,
        "model_name": health.get("model_name") or KRONOS_MODEL_NAME,
        "tokenizer_name": health.get("tokenizer_name") or KRONOS_TOKENIZER_NAME,
        "device": health.get("device") or "unloaded",
        "model_loaded": bool(health.get("model_loaded")),
        "errors": health.get("errors") or [],
    }


@router.post("/forecast")
def kronos_forecast(payload: KronosForecastApiRequest, _admin=Depends(get_current_admin)):
    if payload.fetch_from_polygon:
        bars = fetch_polygon_daily_bars(payload.symbol, lookback_days=240)
    elif payload.bars:
        bars = pd.DataFrame(payload.bars)
    else:
        raise HTTPException(status_code=400, detail="Provide bars or set fetch_from_polygon=true.")

    if bars.empty:
        raise HTTPException(status_code=400, detail="No OHLCV bars were provided.")
    signal = forecast_signal(payload.symbol, payload.timeframe, dataframe_to_kronos_bars(bars), payload.forecast_bars or KRONOS_FORECAST_BARS)
    return signal.forecast.model_dump(mode="json")
