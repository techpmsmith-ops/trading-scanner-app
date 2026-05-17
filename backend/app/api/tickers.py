from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticker
from app.schemas import TickerCreate, TickerRead, TickerUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/tickers", tags=["tickers"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[TickerRead])
def list_tickers(db: Session = Depends(get_db)):
    return db.query(Ticker).order_by(Ticker.symbol.asc()).all()


@router.post("", response_model=TickerRead, status_code=201)
def create_ticker(payload: TickerCreate, db: Session = Depends(get_db)):
    ticker = Ticker(**payload.model_dump())
    db.add(ticker)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ticker already exists") from exc
    db.refresh(ticker)
    return ticker


@router.patch("/{symbol}", response_model=TickerRead)
def update_ticker(symbol: str, payload: TickerUpdate, db: Session = Depends(get_db)):
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol.upper()).one_or_none()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticker, key, value)
    db.commit()
    db.refresh(ticker)
    return ticker


@router.delete("/{symbol}", status_code=204)
def delete_ticker(symbol: str, db: Session = Depends(get_db)):
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol.upper()).one_or_none()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    ticker.active = False
    db.commit()
