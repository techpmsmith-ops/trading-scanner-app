import math
from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Ticker
from app.services.indicators import calculate_indicators
from app.services.market_data import bars_for_ticker, fetch_daily_bars, upsert_price_bars

TIMEFRAME_RULES = {
    "daily": None,
    "weekly": "W-FRI",
    "monthly": "ME",
}

TRADING_PERIODS = {
    "daily": 252,
    "weekly": 52,
    "monthly": 12,
}

STRATEGY_NAMES = {
    "trend_following": "Trend Following",
    "momentum_strength": "Momentum Strength",
    "breakout": "Breakout",
    "mean_reversion": "Mean Reversion",
    "ai_composite": "AI-Assisted Composite",
}


@dataclass
class BacktestRequest:
    symbols: list[str]
    timeframe: str = "daily"
    strategies: list[str] | None = None
    lookback_days: int = 756
    initial_capital: float = 10_000


def run_backtest(db: Session, request: BacktestRequest) -> dict:
    strategies = request.strategies or list(STRATEGY_NAMES)
    symbols = [symbol.strip().upper() for symbol in request.symbols if symbol.strip()]
    if request.timeframe not in TIMEFRAME_RULES:
        raise ValueError("Unsupported timeframe")

    reports = []
    for symbol in symbols:
        bars = _bars_for_symbol(db, symbol, request.lookback_days)
        if len(bars) < 80:
            reports.append({"symbol": symbol, "error": "Not enough historical data for backtest"})
            continue
        frame = _resample(bars, request.timeframe)
        frame = calculate_indicators(frame)
        for strategy in strategies:
            if strategy not in STRATEGY_NAMES:
                continue
            reports.append(_run_strategy(symbol, strategy, frame, request.timeframe, request.initial_capital))

    valid = [item for item in reports if "error" not in item]
    return {
        "timeframe": request.timeframe,
        "initial_capital": request.initial_capital,
        "symbols": symbols,
        "strategies": strategies,
        "results": reports,
        "comparison": sorted(valid, key=lambda item: item["metrics"]["sharpe_ratio"], reverse=True),
        "disclaimer": "Backtests are historical research only. They do not predict future results and are not trade recommendations.",
    }


def _bars_for_symbol(db: Session, symbol: str, lookback_days: int) -> pd.DataFrame:
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol).one_or_none()
    if not ticker:
        ticker = Ticker(symbol=symbol, active=True)
        db.add(ticker)
        db.commit()
        db.refresh(ticker)
    existing = bars_for_ticker(db, ticker)
    if len(existing) < min(lookback_days * 0.5, 220):
        downloaded = fetch_daily_bars(symbol, lookback_days=lookback_days)
        upsert_price_bars(db, ticker, downloaded)
        existing = bars_for_ticker(db, ticker)
    return existing.tail(lookback_days)


def _resample(bars: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = bars.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    rule = TIMEFRAME_RULES[timeframe]
    if not rule:
        return df
    return (
        df.set_index("date")
        .resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "adjusted_close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )


def _run_strategy(symbol: str, strategy: str, frame: pd.DataFrame, timeframe: str, initial_capital: float) -> dict:
    df = frame.copy().dropna(subset=["close"])
    df["signal"] = _signal(strategy, df).astype(int)
    df["market_return"] = df["close"].pct_change().fillna(0)
    df["strategy_return"] = df["signal"].shift(1).fillna(0) * df["market_return"]
    df["equity"] = initial_capital * (1 + df["strategy_return"]).cumprod()
    df["benchmark_equity"] = initial_capital * (1 + df["market_return"]).cumprod()
    trades = _trades(df)
    metrics = _metrics(df, trades, timeframe)
    return {
        "symbol": symbol,
        "strategy": strategy,
        "strategy_name": STRATEGY_NAMES[strategy],
        "timeframe": timeframe,
        "metrics": metrics,
        "trades": trades[-25:],
        "equity_curve": [
            {
                "date": str(row.date.date() if hasattr(row.date, "date") else row.date),
                "equity": round(float(row.equity), 2),
                "benchmark_equity": round(float(row.benchmark_equity), 2),
            }
            for row in df[["date", "equity", "benchmark_equity"]].tail(240).itertuples(index=False)
        ],
        "notes": _strategy_notes(strategy),
    }


def _signal(strategy: str, df: pd.DataFrame) -> pd.Series:
    close = df["close"]
    if strategy == "trend_following":
        return (close > df["sma_50"]) & (df["sma_50"] > df["sma_200"]) & (df["sma_50_slope"] > 0)
    if strategy == "momentum_strength":
        return (close > df["ema_20"]) & (df["macd_histogram"] > 0) & (df["rsi_14"].between(55, 75))
    if strategy == "breakout":
        return (close >= df["high_20"].shift(1)) & (df["relative_volume"] > 1.1) & (close > df["sma_50"])
    if strategy == "mean_reversion":
        return (df["rsi_14"] < 35) & (close >= df["sma_200"] * 0.9)
    composite = (
        (close > df["ema_20"]).astype(int)
        + (close > df["sma_50"]).astype(int)
        + (close > df["sma_200"]).astype(int)
        + (df["macd_histogram"] > 0).astype(int)
        + (df["rsi_14"].between(50, 72)).astype(int)
        + (df["relative_volume"] > 1.0).astype(int)
    )
    return composite >= 4


def _trades(df: pd.DataFrame) -> list[dict]:
    trades: list[dict] = []
    in_trade = False
    entry_price = 0.0
    entry_date = None
    for row in df.itertuples(index=False):
        signal = int(row.signal)
        if signal and not in_trade:
            in_trade = True
            entry_price = float(row.close)
            entry_date = row.date
        elif not signal and in_trade:
            exit_price = float(row.close)
            trades.append(_trade(entry_date, row.date, entry_price, exit_price))
            in_trade = False
    if in_trade:
        last = df.iloc[-1]
        trades.append(_trade(entry_date, last["date"], entry_price, float(last["close"]), open_trade=True))
    return trades


def _trade(entry_date, exit_date, entry_price: float, exit_price: float, open_trade: bool = False) -> dict:
    ret = ((exit_price - entry_price) / entry_price) * 100 if entry_price else 0
    return {
        "entry_date": str(entry_date.date() if hasattr(entry_date, "date") else entry_date),
        "exit_date": str(exit_date.date() if hasattr(exit_date, "date") else exit_date),
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "return_pct": round(ret, 2),
        "result": "open" if open_trade else "win" if ret > 0 else "loss" if ret < 0 else "breakeven",
    }


def _metrics(df: pd.DataFrame, trades: list[dict], timeframe: str) -> dict:
    returns = df["strategy_return"].fillna(0)
    equity = df["equity"]
    total_return = ((equity.iloc[-1] / equity.iloc[0]) - 1) * 100 if len(equity) > 1 else 0
    periods = TRADING_PERIODS[timeframe]
    volatility = returns.std() * math.sqrt(periods) * 100 if len(returns) > 2 else 0
    sharpe = (returns.mean() / returns.std()) * math.sqrt(periods) if returns.std() else 0
    running_max = equity.cummax()
    drawdown = ((equity - running_max) / running_max) * 100
    closed = [trade for trade in trades if trade["result"] != "open"]
    wins = [trade for trade in closed if trade["return_pct"] > 0]
    losses = [trade for trade in closed if trade["return_pct"] < 0]
    gross_gain = sum(trade["return_pct"] for trade in wins)
    gross_loss = abs(sum(trade["return_pct"] for trade in losses))
    return {
        "total_return_pct": round(total_return, 2),
        "annualized_volatility_pct": round(volatility, 2),
        "sharpe_ratio": round(float(sharpe), 3),
        "max_drawdown_pct": round(float(drawdown.min()), 2),
        "trade_count": len(closed),
        "win_rate_pct": round((len(wins) / len(closed)) * 100, 2) if closed else 0,
        "average_trade_return_pct": round(sum(trade["return_pct"] for trade in closed) / len(closed), 2) if closed else 0,
        "profit_factor": round(gross_gain / gross_loss, 3) if gross_loss else None,
        "final_equity": round(float(equity.iloc[-1]), 2),
    }


def _strategy_notes(strategy: str) -> str:
    if strategy == "ai_composite":
        return "Transparent AI-assisted comparison profile using multiple scanner-style indicator votes; not a black-box model."
    return "Rule-based historical strategy profile for research and comparison only."
