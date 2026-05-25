from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    IntelligenceDashboard,
    IntelligenceWatchlistCreate,
    IntelligenceWatchlistRead,
    IntelligenceWatchlistUpdate,
)
from app.services.auth import get_current_admin, get_current_user
from app.services.intelligence import (
    intelligence_dashboard,
    list_watchlist,
    update_watchlist_symbol,
    upsert_watchlist_symbol,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"], dependencies=[Depends(get_current_user)])


@router.get("/dashboard", response_model=IntelligenceDashboard)
def dashboard(db: Session = Depends(get_db)):
    return intelligence_dashboard(db)


@router.get("/watchlist", response_model=list[IntelligenceWatchlistRead])
def get_watchlist(include_inactive: bool = False, db: Session = Depends(get_db)):
    return list_watchlist(db, include_inactive=include_inactive)


@router.post("/watchlist", response_model=IntelligenceWatchlistRead)
def create_or_replace_watchlist_symbol(
    payload: IntelligenceWatchlistCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return upsert_watchlist_symbol(db, payload.model_dump())


@router.patch("/watchlist/{symbol}", response_model=IntelligenceWatchlistRead)
def patch_watchlist_symbol(
    symbol: str,
    payload: IntelligenceWatchlistUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    row = update_watchlist_symbol(db, symbol, payload.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(status_code=404, detail="Watchlist symbol not found")
    return row
