from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ResearchPosition
from app.schemas import ResearchPortfolioDashboard, ResearchPositionCreate, ResearchPositionRead, ResearchPositionUpdate
from app.services.auth import get_current_user
from app.services.research_portfolio import portfolio_dashboard, serialize_position

router = APIRouter(prefix="/research-portfolio", tags=["research portfolio"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ResearchPortfolioDashboard)
def dashboard(db: Session = Depends(get_db)):
    return portfolio_dashboard(db)


@router.post("/positions", response_model=ResearchPositionRead, status_code=201)
def create_position(payload: ResearchPositionCreate, db: Session = Depends(get_db)):
    row = ResearchPosition(**payload.model_dump())
    if row.position_type == "leaps" and row.break_even is None and row.strike_price is not None and row.premium_paid is not None:
        row.break_even = round(row.strike_price + row.premium_paid, 2)
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_position(row)


@router.patch("/positions/{position_id}", response_model=ResearchPositionRead)
def update_position(position_id: int, payload: ResearchPositionUpdate, db: Session = Depends(get_db)):
    row = db.query(ResearchPosition).filter(ResearchPosition.id == position_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Research position not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    if row.position_type == "leaps" and row.break_even is None and row.strike_price is not None and row.premium_paid is not None:
        row.break_even = round(row.strike_price + row.premium_paid, 2)
    db.commit()
    db.refresh(row)
    return serialize_position(row)


@router.delete("/positions/{position_id}", status_code=204)
def delete_position(position_id: int, db: Session = Depends(get_db)):
    row = db.query(ResearchPosition).filter(ResearchPosition.id == position_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Research position not found")
    db.delete(row)
    db.commit()
