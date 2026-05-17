from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JournalEntry
from app.schemas import JournalCreate, JournalRead, JournalUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/journal", tags=["journal"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[JournalRead])
def list_entries(symbol: str | None = None, status: str | None = None, result: str | None = None, db: Session = Depends(get_db)):
    query = db.query(JournalEntry)
    if symbol:
        query = query.filter(JournalEntry.symbol == symbol.upper())
    if status:
        query = query.filter(JournalEntry.status == status)
    if result:
        query = query.filter(JournalEntry.result == result)
    return query.order_by(JournalEntry.created_at.desc()).all()


@router.post("", response_model=JournalRead, status_code=201)
def create_entry(payload: JournalCreate, db: Session = Depends(get_db)):
    if payload.linked_scan_result_id:
        duplicate = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.linked_scan_result_id == payload.linked_scan_result_id,
                JournalEntry.status.in_(["planned", "open"]),
            )
            .one_or_none()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="This scan result is already linked to an active journal entry")
    entry = JournalEntry(**payload.model_dump())
    calculate_pnl(entry)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=JournalRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.patch("/{entry_id}", response_model=JournalRead)
def update_entry(entry_id: int, payload: JournalUpdate, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "symbol" and value:
            value = value.upper()
        setattr(entry, key, value)
    calculate_pnl(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()


def calculate_pnl(entry: JournalEntry) -> None:
    if entry.actual_entry is None or entry.exit_price is None:
        return
    size = entry.position_size or 1
    multiplier = -1 if entry.direction == "short" else 1
    entry.pnl_amount = round((entry.exit_price - entry.actual_entry) * size * multiplier, 2)
    entry.pnl_percent = round(((entry.exit_price - entry.actual_entry) / entry.actual_entry) * 100 * multiplier, 2)
    if entry.result is None:
        if entry.pnl_amount > 0:
            entry.result = "win"
        elif entry.pnl_amount < 0:
            entry.result = "loss"
        else:
            entry.result = "breakeven"
