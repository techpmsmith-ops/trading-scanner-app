from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import PHASE2_PREDICTION_SYMBOLS
from app.database import get_db
from app.models import AlertSubscription, DailyRecommendation, WeeklyEvaluationReport, WeeklyPrediction
from app.schemas import (
    AlertSubscriptionCreate,
    AlertSubscriptionRead,
    AlertSubscriptionUpdate,
    AlertTestResponse,
    DailyRecommendationRead,
    Phase2Dashboard,
    ScoringWeightRead,
    WeeklyEvaluationReportRead,
    WeeklyPredictionRead,
)
from app.services.alerts import send_alerts, send_channel
from app.services.auth import get_current_admin, get_current_user
from app.services.phase2 import (
    evaluate_weekly_predictions,
    generate_daily_top_five,
    generate_weekly_predictions,
    latest_evaluation_report,
    latest_weight_row,
    regenerate_current_week_predictions,
)

router = APIRouter(prefix="/phase2", tags=["phase2"], dependencies=[Depends(get_current_user)])


@router.get("/dashboard", response_model=Phase2Dashboard)
def dashboard(db: Session = Depends(get_db)):
    return {
        "daily_top_five": latest_daily_top_five(db),
        "weekly_predictions": latest_weekly_predictions(db),
        "scoring_weights": latest_weight_row(db),
        "latest_evaluation": latest_evaluation_report(db),
        "prediction_symbols": PHASE2_PREDICTION_SYMBOLS,
    }


@router.post("/recommendations/generate", response_model=list[DailyRecommendationRead])
def create_recommendations(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    rows = generate_daily_top_five(db)
    if rows:
        send_alerts(db, "daily_top_five", "Daily top-five watchlist signals:\n" + "\n".join([f"{row.rank}. {row.symbol} {row.score_total}/100" for row in rows]))
    return rows


@router.get("/recommendations/latest", response_model=list[DailyRecommendationRead])
def get_recommendations(db: Session = Depends(get_db)):
    return latest_daily_top_five(db)


@router.post("/predictions/generate", response_model=list[WeeklyPredictionRead])
def create_predictions(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    rows = generate_weekly_predictions(db)
    if rows:
        send_alerts(db, "weekly_predictions", "Weekly prediction tracking:\n" + "\n".join([f"{row.symbol}: {row.direction} ({row.confidence:.0%})" for row in rows]))
    return rows


@router.post("/predictions/regenerate-current-week", response_model=list[WeeklyPredictionRead])
def regenerate_predictions(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    rows = regenerate_current_week_predictions(db)
    if rows:
        send_alerts(db, "weekly_predictions", "Weekly predictions regenerated for the current market week:\n" + "\n".join([f"{row.symbol}: {row.direction} ({row.confidence:.0%})" for row in rows]))
    return rows


@router.post("/predictions/evaluate", response_model=list[WeeklyPredictionRead])
def evaluate_predictions(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return evaluate_weekly_predictions(db)


@router.get("/evaluations/latest", response_model=WeeklyEvaluationReportRead | None)
def get_latest_evaluation(db: Session = Depends(get_db)):
    return latest_evaluation_report(db)


@router.get("/evaluations", response_model=list[WeeklyEvaluationReportRead])
def get_evaluations(db: Session = Depends(get_db)):
    return db.query(WeeklyEvaluationReport).order_by(WeeklyEvaluationReport.created_at.desc()).limit(20).all()


@router.get("/predictions", response_model=list[WeeklyPredictionRead])
def get_predictions(db: Session = Depends(get_db)):
    return db.query(WeeklyPrediction).order_by(WeeklyPrediction.week_start.desc(), WeeklyPrediction.symbol.asc()).limit(50).all()


@router.get("/weights/latest", response_model=ScoringWeightRead | None)
def get_weights(db: Session = Depends(get_db)):
    return latest_weight_row(db)


@router.get("/alerts", response_model=list[AlertSubscriptionRead])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(AlertSubscription).order_by(AlertSubscription.channel.asc()).all()


@router.post("/alerts", response_model=AlertSubscriptionRead)
def create_alert(payload: AlertSubscriptionCreate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    row = AlertSubscription(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/alerts/{alert_id}", response_model=AlertSubscriptionRead)
def update_alert(alert_id: int, payload: AlertSubscriptionUpdate, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    row = db.query(AlertSubscription).filter(AlertSubscription.id == alert_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Alert subscription not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.post("/alerts/test/{channel}", response_model=AlertTestResponse)
def test_alert(channel: str, _admin=Depends(get_current_admin)):
    return send_channel(channel, "Trading Scanner test alert. Educational watchlist notifications are configured.")


def latest_daily_top_five(db: Session):
    return (
        db.query(DailyRecommendation)
        .order_by(DailyRecommendation.recommendation_date.desc(), DailyRecommendation.rank.asc())
        .limit(5)
        .all()
    )


def latest_weekly_predictions(db: Session):
    return (
        db.query(WeeklyPrediction)
        .order_by(WeeklyPrediction.week_start.desc(), WeeklyPrediction.symbol.asc())
        .limit(len(PHASE2_PREDICTION_SYMBOLS))
        .all()
    )
