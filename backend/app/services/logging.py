import json
import logging
from datetime import date, datetime
from typing import Any


logger = logging.getLogger("trading_scanner")


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, default=_json_default, separators=(",", ":")))


def log_warning(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.warning(json.dumps(payload, default=_json_default, separators=(",", ":")))


def log_exception(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.exception(json.dumps(payload, default=_json_default, separators=(",", ":")))
