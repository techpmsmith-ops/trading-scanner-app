import base64

import requests
from sqlalchemy.orm import Session

from app.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    TWILIO_TO_NUMBER,
)
from app.models import AlertSubscription
from app.services.logging import log_event, log_warning


def send_alerts(db: Session, alert_type: str, message: str) -> list[dict]:
    subscriptions = (
        db.query(AlertSubscription)
        .filter(AlertSubscription.enabled.is_(True))
        .all()
    )
    results: list[dict] = []
    for subscription in subscriptions:
        if alert_type not in (subscription.alert_types or []):
            continue
        results.append(send_channel(subscription.channel, message))
    return results


def send_channel(channel: str, message: str) -> dict:
    if channel == "telegram":
        return send_telegram(message)
    if channel == "sms":
        return send_sms(message)
    return {"channel": channel, "configured": False, "sent": False, "detail": "Unsupported channel"}


def send_telegram(message: str) -> dict:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"channel": "telegram", "configured": False, "sent": False, "detail": "Telegram env vars are not configured"}
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
        response.raise_for_status()
        log_event("alert_sent", channel="telegram")
        return {"channel": "telegram", "configured": True, "sent": True, "detail": "Sent"}
    except Exception as exc:
        log_warning("alert_failed", channel="telegram", error=str(exc))
        return {"channel": "telegram", "configured": True, "sent": False, "detail": str(exc)}


def send_sms(message: str) -> dict:
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER]):
        return {"channel": "sms", "configured": False, "sent": False, "detail": "Twilio env vars are not configured"}
    try:
        auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
            data={"From": TWILIO_FROM_NUMBER, "To": TWILIO_TO_NUMBER, "Body": message[:1500]},
            headers={"Authorization": f"Basic {auth}"},
            timeout=10,
        )
        response.raise_for_status()
        log_event("alert_sent", channel="sms")
        return {"channel": "sms", "configured": True, "sent": True, "detail": "Sent"}
    except Exception as exc:
        log_warning("alert_failed", channel="sms", error=str(exc))
        return {"channel": "sms", "configured": True, "sent": False, "detail": str(exc)}
