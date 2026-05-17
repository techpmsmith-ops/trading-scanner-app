from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JournalEntry
from app.schemas import PerformanceSummary
from app.services.auth import get_current_user

router = APIRouter(prefix="/performance", tags=["performance"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=PerformanceSummary)
def performance_summary(db: Session = Depends(get_db)):
    trades = db.query(JournalEntry).filter(JournalEntry.status == "closed").all()
    wins = [trade for trade in trades if trade.result == "win"]
    losses = [trade for trade in trades if trade.result == "loss"]
    breakeven = [trade for trade in trades if trade.result == "breakeven"]
    pnl_values = [trade.pnl_amount for trade in trades if trade.pnl_amount is not None]
    gain_values = [trade.pnl_amount for trade in wins if trade.pnl_amount is not None]
    loss_values = [trade.pnl_amount for trade in losses if trade.pnl_amount is not None]
    tags = Counter(tag for trade in trades for tag in (trade.mistake_tags or []))

    total = len(trades)
    return {
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven_trades": len(breakeven),
        "win_rate": round((len(wins) / total) * 100, 2) if total else 0,
        "average_gain": round(sum(gain_values) / len(gain_values), 2) if gain_values else 0,
        "average_loss": round(sum(loss_values) / len(loss_values), 2) if loss_values else 0,
        "total_pnl": round(sum(pnl_values), 2) if pnl_values else 0,
        "best_trade": max(pnl_values) if pnl_values else None,
        "worst_trade": min(pnl_values) if pnl_values else None,
        "most_common_mistake_tags": [{"tag": tag, "count": count} for tag, count in tags.most_common(10)],
    }
