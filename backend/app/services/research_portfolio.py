from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.config import DEFAULT_TICKER_METADATA
from app.models import ResearchPosition, Ticker

BASE_GOAL = 250_000
STRETCH_GOAL = 400_000
GOAL_DATE = date(2026, 12, 31)


def ensure_research_tickers(db: Session) -> None:
    symbols = [row[0] for row in db.query(ResearchPosition.symbol).distinct().all()]
    for symbol in symbols:
        ensure_research_ticker(db, symbol)
    db.commit()


def ensure_research_ticker(db: Session, symbol: str) -> Ticker:
    normalized = symbol.strip().upper()
    metadata = DEFAULT_TICKER_METADATA.get(normalized, {})
    ticker = db.query(Ticker).filter(Ticker.symbol == normalized).one_or_none()
    if not ticker:
        ticker = Ticker(
            symbol=normalized,
            name=metadata.get("name"),
            asset_type=metadata.get("asset_type", "stock"),
            active=True,
        )
        db.add(ticker)
    else:
        ticker.active = True
        if not ticker.name and metadata.get("name"):
            ticker.name = metadata["name"]
        if ticker.asset_type == "stock" and metadata.get("asset_type"):
            ticker.asset_type = metadata["asset_type"]
    return ticker


def sync_share_positions_from_scan(db: Session, symbol: str, close_price: float) -> None:
    positions = (
        db.query(ResearchPosition)
        .filter(ResearchPosition.symbol == symbol.upper(), ResearchPosition.position_type == "shares")
        .all()
    )
    for position in positions:
        position.current_price = close_price


def position_market_value(position: ResearchPosition) -> float:
    if position.position_type == "leaps":
        return round((position.contracts or 0) * 100 * (position.current_contract_price or 0), 2)
    return round((position.quantity or 0) * (position.current_price or 0), 2)


def position_cost_basis(position: ResearchPosition) -> float:
    if position.position_type == "leaps":
        return round((position.contracts or 0) * 100 * (position.premium_paid or 0), 2)
    return round((position.quantity or 0) * (position.average_cost or 0), 2)


def serialize_position(position: ResearchPosition) -> dict:
    value = position_market_value(position)
    cost = position_cost_basis(position)
    pnl = round(value - cost, 2)
    return {
        **position.__dict__,
        "market_value": value,
        "cost_basis": cost,
        "unrealized_pnl": pnl,
        "unrealized_pnl_pct": round((pnl / cost) * 100, 2) if cost else None,
    }


def portfolio_dashboard(db: Session) -> dict:
    positions = db.query(ResearchPosition).order_by(ResearchPosition.symbol.asc(), ResearchPosition.position_type.asc()).all()
    serialized = [serialize_position(position) for position in positions]
    return {"positions": serialized, "summary": portfolio_summary(serialized)}


def portfolio_summary(positions: list[dict]) -> dict:
    current_value = round(sum(item["market_value"] for item in positions), 2)
    cost_basis = round(sum(item["cost_basis"] for item in positions), 2)
    unrealized = round(current_value - cost_basis, 2)
    shares_value = round(sum(item["market_value"] for item in positions if item["position_type"] == "shares"), 2)
    leaps_value = round(sum(item["market_value"] for item in positions if item["position_type"] == "leaps"), 2)
    return {
        "current_value": current_value,
        "cost_basis": cost_basis,
        "unrealized_pnl": unrealized,
        "unrealized_pnl_pct": round((unrealized / cost_basis) * 100, 2) if cost_basis else None,
        "shares_value": shares_value,
        "leaps_value": leaps_value,
        "leaps_exposure_pct": round((leaps_value / current_value) * 100, 2) if current_value else 0,
        "positions_count": len(positions),
        "goals": [_goal_path("Base goal", BASE_GOAL, current_value), _goal_path("Stretch goal", STRETCH_GOAL, current_value)],
        "theme_allocations": _allocations(positions, "theme"),
        "role_allocations": _allocations(positions, "role"),
    }


def _goal_path(label: str, target: float, current_value: float) -> dict:
    months = max(0.1, (GOAL_DATE - date.today()).days / 30.4375)
    gap = round(target - current_value, 2)
    required_return = ((target / current_value) - 1) * 100 if current_value else None
    monthly = (((target / current_value) ** (1 / months)) - 1) * 100 if current_value else None
    return {
        "label": label,
        "target_value": target,
        "gap": gap,
        "required_return_pct": round(required_return, 2) if required_return is not None else None,
        "required_monthly_return_pct": round(monthly, 2) if monthly is not None else None,
        "months_remaining": round(months, 1),
    }


def _allocations(positions: list[dict], key: str) -> list[dict]:
    totals: dict[str, float] = defaultdict(float)
    current_value = sum(item["market_value"] for item in positions)
    for item in positions:
        label = item.get(key) or "Unassigned"
        totals[label] += item["market_value"]
    return [
        {"name": name, "market_value": round(value, 2), "allocation_pct": round((value / current_value) * 100, 2) if current_value else 0}
        for name, value in sorted(totals.items(), key=lambda row: row[1], reverse=True)
    ]
