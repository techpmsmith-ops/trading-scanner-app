from __future__ import annotations

import sys
from pathlib import Path
from threading import Lock

import pandas as pd

from app.config import KRONOS_DEVICE, KRONOS_FORECAST_BARS, KRONOS_LOOKBACK_BARS, KRONOS_MODEL_NAME, KRONOS_TOKENIZER_NAME
from app.services.kronos.kronos_adapter import build_result_from_prediction, unavailable_result, validate_ohlcv
from app.services.kronos.kronos_schema import KronosBar, KronosForecastResult


class KronosClient:
    def __init__(
        self,
        model_name: str = KRONOS_MODEL_NAME,
        tokenizer_name: str = KRONOS_TOKENIZER_NAME,
        device: str = KRONOS_DEVICE,
        lookback_bars: int = KRONOS_LOOKBACK_BARS,
    ):
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.requested_device = device
        self.lookback_bars = lookback_bars
        self._lock = Lock()
        self._predictor = None
        self._load_error: str | None = None
        self._device = "unloaded"

    @property
    def model_loaded(self) -> bool:
        return self._predictor is not None

    @property
    def device(self) -> str:
        return self._device

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def health(self) -> dict:
        return {
            "model_name": self.model_name,
            "tokenizer_name": self.tokenizer_name,
            "device": self.device,
            "model_loaded": self.model_loaded,
            "errors": [self._load_error] if self._load_error else [],
        }

    def load(self) -> None:
        if self._predictor is not None:
            return
        with self._lock:
            if self._predictor is not None:
                return
            try:
                root = Path(__file__).resolve().parents[4]
                kronos_root = root / "external" / "Kronos"
                if str(kronos_root) not in sys.path:
                    sys.path.insert(0, str(kronos_root))
                from model import Kronos, KronosPredictor, KronosTokenizer

                tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_name)
                model = Kronos.from_pretrained(self.model_name)
                device = None if self.requested_device == "auto" else self.requested_device
                max_context = 2048 if "mini" in self.model_name.lower() else 512
                self._predictor = KronosPredictor(model, tokenizer, device=device, max_context=max_context)
                self._device = self._predictor.device
                self._load_error = None
            except Exception as exc:
                self._load_error = str(exc)
                self._device = "unavailable"
                raise

    def predict(self, symbol: str, timeframe: str, bars: list[KronosBar], forecast_bars: int | None = None) -> KronosForecastResult:
        forecast_bars = forecast_bars or KRONOS_FORECAST_BARS
        ok, warnings = validate_ohlcv(bars, self.lookback_bars)
        if not ok:
            return unavailable_result(symbol, timeframe, self.model_name, warnings[0], warnings)
        try:
            self.load()
            context = bars[-self.lookback_bars :]
            df = pd.DataFrame([bar.model_dump() for bar in context])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if "amount" not in df or df["amount"].isna().all():
                df["amount"] = df["volume"] * df[["open", "high", "low", "close"]].mean(axis=1)
            x_df = df[["open", "high", "low", "close", "volume", "amount"]]
            x_timestamp = df["timestamp"]
            y_timestamp = _future_timestamps(x_timestamp.iloc[-1], timeframe, forecast_bars)
            prediction = self._predictor.predict(
                x_df,
                x_timestamp,
                y_timestamp,
                pred_len=forecast_bars,
                sample_count=1,
                verbose=False,
            )
            result = build_result_from_prediction(symbol, timeframe, self.model_name, context, prediction)
            result.warnings.extend(warnings)
            return result
        except Exception as exc:
            return unavailable_result(symbol, timeframe, self.model_name, str(exc), warnings)


def _future_timestamps(latest_timestamp, timeframe: str, forecast_bars: int) -> pd.Series:
    latest = pd.to_datetime(latest_timestamp)
    if timeframe in {"1d", "daily", "day"}:
        return pd.Series(pd.bdate_range(latest + pd.Timedelta(days=1), periods=forecast_bars))
    if timeframe.endswith("m"):
        minutes = int(timeframe[:-1])
        return pd.Series([latest + pd.Timedelta(minutes=minutes * step) for step in range(1, forecast_bars + 1)])
    return pd.Series([latest + pd.Timedelta(days=step) for step in range(1, forecast_bars + 1)])


_client: KronosClient | None = None


def get_kronos_client() -> KronosClient:
    global _client
    if _client is None:
        _client = KronosClient()
    return _client
