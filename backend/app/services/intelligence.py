from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import FOCUS_GROUP_SYMBOLS
from app.models import (
    FocusGroupAnalysis,
    IntelligenceWatchlistSymbol,
    ScanResult,
    ScanRun,
    WeeklyEvaluationReport,
    WeeklyPrediction,
)


MISSION = (
    "Continuously surface asymmetric AI infrastructure opportunities by combining scanner signals, "
    "focus-group research, prediction feedback, risk controls, and modular agent simulations."
)

DEFAULT_DATA_SOURCES = [
    "Polygon.io",
    "Finnhub",
    "Alpaca",
    "TradingView indicators",
    "SEC filings",
    "Earnings calendars",
    "News APIs",
    "Social sentiment APIs",
    "Reddit sentiment",
    "X/Twitter sentiment",
    "YouTube financial sentiment",
]

INITIAL_WATCHLIST = {
    "INTC": {
        "company_name": "Intel",
        "themes": ["semiconductors", "foundry", "AI PCs", "data center"],
        "thesis": "Turnaround and domestic foundry optionality with cyclical semiconductor leverage.",
    },
    "NVDA": {
        "company_name": "NVIDIA",
        "themes": ["AI accelerators", "data center", "networking", "software ecosystem"],
        "thesis": "Category leader for AI infrastructure compute with platform-level upside and valuation risk.",
    },
    "AMD": {
        "company_name": "Advanced Micro Devices",
        "themes": ["AI accelerators", "CPUs", "data center", "edge AI"],
        "thesis": "Second-source accelerator and CPU exposure with room for AI share gains.",
    },
    "IONQ": {
        "company_name": "IonQ",
        "themes": ["quantum computing", "advanced computing"],
        "thesis": "High-volatility quantum computing exposure with long-duration asymmetric optionality.",
    },
    "NVTS": {
        "company_name": "Navitas Semiconductor",
        "themes": ["power semiconductors", "energy efficiency", "data center power"],
        "thesis": "Power efficiency supplier candidate for higher-density AI infrastructure.",
    },
    "RVI": {
        "company_name": "Retail Value Inc.",
        "themes": ["special situation", "monitor"],
        "thesis": "Placeholder monitor slot retained from the initial list until thesis is refined.",
    },
    "SMCI": {
        "company_name": "Super Micro Computer",
        "themes": ["AI servers", "data center", "liquid cooling", "rack-scale systems"],
        "thesis": "Direct AI server buildout exposure with execution and accounting headline risk.",
    },
    "RGTI": {
        "company_name": "Rigetti Computing",
        "themes": ["quantum computing", "advanced computing"],
        "thesis": "Speculative quantum computing exposure sensitive to funding and milestone credibility.",
    },
    "RKLB": {
        "company_name": "Rocket Lab",
        "themes": ["space technology", "defense", "launch", "satellite infrastructure"],
        "thesis": "Space infrastructure and defense optionality with execution-driven upside.",
    },
    "MU": {
        "company_name": "Micron Technology",
        "themes": ["memory", "HBM", "semiconductors", "data center"],
        "thesis": "Memory and HBM cycle exposure tied to AI accelerator supply chains.",
    },
}


MODULES = [
    {
        "key": "market_scanner",
        "name": "Market Scanner Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Rank broad opportunities", "Detect momentum, breakouts, risk flags"],
        "data_sources": ["Price history", "Volume", "Technical indicators"],
        "output_feeds": ["Opportunities", "Daily top five", "Focus analysis"],
    },
    {
        "key": "focus_group_intelligence",
        "name": "Focus Group Intelligence Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Deep daily analysis", "AI infrastructure relevance scoring", "Watchlist expansion"],
        "data_sources": ["Watchlist", "Scanner results", "News sentiment"],
        "output_feeds": ["Focus heatmap", "Confidence rankings", "Alerts"],
    },
    {
        "key": "news_sentiment",
        "name": "News & Sentiment Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Score fresh headlines", "Track catalyst polarity"],
        "data_sources": ["News APIs", "Social sentiment APIs"],
        "output_feeds": ["Confidence score", "Catalyst summary"],
    },
    {
        "key": "prediction",
        "name": "Prediction Engine",
        "phase": 2,
        "status": "active",
        "responsibilities": ["Weekly ranges", "Directional probabilities", "Trade plan drafts"],
        "data_sources": ["Scanner scores", "Focus metrics", "Sentiment"],
        "output_feeds": ["Prediction history", "Learning feedback"],
    },
    {
        "key": "learning_feedback",
        "name": "Learning & Feedback Engine",
        "phase": 2,
        "status": "active",
        "responsibilities": ["Evaluate predictions", "Adjust bounded weights", "Build stock profiles"],
        "data_sources": ["Prediction outcomes", "Indicator effectiveness", "News correlation"],
        "output_feeds": ["Scoring weights", "Confidence calibration"],
    },
    {
        "key": "agent_simulation",
        "name": "AI Agent Simulation Engine",
        "phase": 3,
        "status": "prototype",
        "responsibilities": ["Stress test trade ideas", "Estimate crowding", "Model participant reactions"],
        "data_sources": ["Focus analysis", "Macro scenarios", "Sentiment"],
        "output_feeds": ["Risk score", "Confidence adjustment", "Trade validation"],
    },
    {
        "key": "risk_management",
        "name": "Risk Management Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Flag fragile setups", "Summarize concentration", "Bound confidence"],
        "data_sources": ["Risk flags", "Volatility", "Scenario results"],
        "output_feeds": ["Risk overview", "Alerts"],
    },
    {
        "key": "trade_execution",
        "name": "Trade Execution Engine",
        "phase": 4,
        "status": "planned",
        "responsibilities": ["Manual approval", "Semi-autonomous execution", "Broker integration"],
        "data_sources": ["Validated trade plans", "Portfolio limits", "Alpaca"],
        "output_feeds": ["Orders", "Audit trail"],
    },
    {
        "key": "alerts",
        "name": "Alert & Notification Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Telegram alerts", "Daily summaries", "Signal change notifications"],
        "data_sources": ["Opportunities", "Predictions", "Risk warnings"],
        "output_feeds": ["Telegram", "Dashboard notifications"],
    },
    {
        "key": "backtesting",
        "name": "Historical Backtesting Engine",
        "phase": 1,
        "status": "active",
        "responsibilities": ["Strategy comparisons", "Equity curves", "Drawdown checks"],
        "data_sources": ["Historical bars", "Strategy rules"],
        "output_feeds": ["Research validation", "Risk management"],
    },
    {
        "key": "portfolio_intelligence",
        "name": "Portfolio Intelligence Engine",
        "phase": 4,
        "status": "planned",
        "responsibilities": ["Exposure analysis", "Position sizing", "Style personalization"],
        "data_sources": ["Journal", "Broker positions", "Risk limits"],
        "output_feeds": ["Portfolio exposure", "Optimization"],
    },
    {
        "key": "macro_sector_rotation",
        "name": "Macro & Sector Rotation Engine",
        "phase": 3,
        "status": "prototype",
        "responsibilities": ["Market regime", "Sector leadership", "AI infrastructure trend strength"],
        "data_sources": ["SPY", "QQQ", "Sector ETFs", "Macro events"],
        "output_feeds": ["Theme trends", "Risk regime"],
    },
]


def ensure_default_intelligence_watchlist(db: Session) -> None:
    existing = {row.symbol for row in db.query(IntelligenceWatchlistSymbol).all()}
    for symbol in FOCUS_GROUP_SYMBOLS:
        defaults = INITIAL_WATCHLIST.get(symbol, {"themes": ["advanced technology"], "thesis": "Dynamic focus-group symbol."})
        if symbol not in existing:
            db.add(
                IntelligenceWatchlistSymbol(
                    symbol=symbol,
                    company_name=defaults.get("company_name"),
                    priority="core",
                    active=True,
                    themes=defaults.get("themes", []),
                    thesis=defaults.get("thesis"),
                    data_sources=DEFAULT_DATA_SOURCES,
                )
            )
    db.commit()


def list_watchlist(db: Session, include_inactive: bool = False) -> list[IntelligenceWatchlistSymbol]:
    ensure_default_intelligence_watchlist(db)
    query = db.query(IntelligenceWatchlistSymbol)
    if not include_inactive:
        query = query.filter(IntelligenceWatchlistSymbol.active.is_(True))
    return query.order_by(IntelligenceWatchlistSymbol.priority.asc(), IntelligenceWatchlistSymbol.symbol.asc()).all()


def upsert_watchlist_symbol(db: Session, payload: dict) -> IntelligenceWatchlistSymbol:
    symbol = payload["symbol"].strip().upper()
    row = db.query(IntelligenceWatchlistSymbol).filter(IntelligenceWatchlistSymbol.symbol == symbol).one_or_none()
    if row:
        for key, value in payload.items():
            if key != "symbol":
                setattr(row, key, value)
    else:
        row = IntelligenceWatchlistSymbol(**{**payload, "symbol": symbol})
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_watchlist_symbol(db: Session, symbol: str, payload: dict) -> IntelligenceWatchlistSymbol | None:
    row = db.query(IntelligenceWatchlistSymbol).filter(IntelligenceWatchlistSymbol.symbol == symbol.strip().upper()).one_or_none()
    if not row:
        return None
    for key, value in payload.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def intelligence_dashboard(db: Session) -> dict:
    watchlist = list_watchlist(db)
    focus_by_symbol = _latest_focus_by_symbol(db)
    latest_results = _latest_scan_results(db)
    predictions = _latest_predictions_by_symbol(db)
    opportunities = [_opportunity(row, focus_by_symbol.get(row.symbol), latest_results.get(row.symbol), predictions.get(row.symbol)) for row in watchlist]
    opportunities.sort(key=lambda item: item["conviction_score"], reverse=True)
    simulations = _simulate_scenarios(opportunities)
    return {
        "generated_at": datetime.utcnow(),
        "mission": MISSION,
        "modules": MODULES,
        "watchlist": watchlist,
        "opportunities": opportunities,
        "theme_trends": _theme_trends(watchlist, opportunities),
        "simulations": simulations,
        "prediction_accuracy": _prediction_accuracy(db),
        "risk_overview": _risk_overview(opportunities, simulations),
        "next_actions": _next_actions(opportunities, simulations),
    }


def _latest_focus_by_symbol(db: Session) -> dict[str, FocusGroupAnalysis]:
    rows = db.query(FocusGroupAnalysis).order_by(FocusGroupAnalysis.analysis_date.desc(), FocusGroupAnalysis.created_at.desc()).all()
    output = {}
    for row in rows:
        output.setdefault(row.symbol, row)
    return output


def _latest_scan_results(db: Session) -> dict[str, ScanResult]:
    run = db.query(ScanRun).order_by(ScanRun.started_at.desc()).first()
    if not run:
        return {}
    return {row.symbol: row for row in db.query(ScanResult).filter(ScanResult.scan_run_id == run.id).all()}


def _latest_predictions_by_symbol(db: Session) -> dict[str, WeeklyPrediction]:
    rows = db.query(WeeklyPrediction).order_by(WeeklyPrediction.week_start.desc(), WeeklyPrediction.created_at.desc()).all()
    output = {}
    for row in rows:
        output.setdefault(row.symbol, row)
    return output


def _opportunity(
    watch: IntelligenceWatchlistSymbol,
    focus: FocusGroupAnalysis | None,
    result: ScanResult | None,
    prediction: WeeklyPrediction | None,
) -> dict:
    scan_score = result.score_total if result else 50
    focus_confidence = (focus.confidence * 100) if focus else 45
    prediction_confidence = (prediction.confidence * 100) if prediction else 45
    momentum_score = _bounded((result.score_momentum if result else 10) * 5)
    risk_score = _risk_score(focus, result)
    ai_relevance = _theme_relevance(watch.themes or [])
    institutional = _institutional_interest(result, focus)
    asymmetric = _bounded((ai_relevance * 0.45) + (scan_score * 0.25) + (prediction_confidence * 0.2) + (momentum_score * 0.1) - (risk_score * 0.18))
    conviction = _bounded((scan_score * 0.3) + (focus_confidence * 0.25) + (prediction_confidence * 0.2) + (ai_relevance * 0.15) + (institutional * 0.1) - (risk_score * 0.15))
    bias = focus.bias if focus else prediction.direction if prediction else ("bullish" if conviction >= 65 else "neutral")
    return {
        "symbol": watch.symbol,
        "bias": bias,
        "conviction_score": round(conviction, 1),
        "asymmetric_score": round(asymmetric, 1),
        "momentum_score": round(momentum_score, 1),
        "risk_score": round(risk_score, 1),
        "ai_relevance_score": round(ai_relevance, 1),
        "institutional_interest_score": round(institutional, 1),
        "time_horizon": "long-term asymmetric" if asymmetric >= 70 else "swing/momentum" if momentum_score >= 65 else "research watch",
        "catalysts": _catalysts(watch, focus, prediction),
        "risks": _risks(focus, result, prediction),
        "action": _action(conviction, asymmetric, risk_score, bias),
    }


def _bounded(value: float, floor: float = 0, ceiling: float = 100) -> float:
    return max(floor, min(ceiling, value))


def _risk_score(focus: FocusGroupAnalysis | None, result: ScanResult | None) -> float:
    base = 35
    if focus and focus.risk_level == "high":
        base += 35
    elif focus and focus.risk_level == "medium":
        base += 18
    if result:
        base += min(25, len(result.risk_flags or []) * 8)
        atr = (result.indicators or {}).get("atr_percent") or 0
        base += min(15, float(atr))
    return _bounded(base)


def _theme_relevance(themes: list[str]) -> float:
    score = 35
    keywords = {
        "AI": 18,
        "accelerator": 16,
        "data center": 16,
        "semiconductor": 14,
        "memory": 12,
        "HBM": 14,
        "power": 10,
        "cooling": 10,
        "quantum": 12,
        "defense": 10,
        "space": 8,
        "robotics": 8,
    }
    text = " ".join(themes).lower()
    for keyword, points in keywords.items():
        if keyword.lower() in text:
            score += points
    return _bounded(score)


def _institutional_interest(result: ScanResult | None, focus: FocusGroupAnalysis | None) -> float:
    score = 40
    if result:
        score += (result.score_volume / 15) * 25
    if focus and focus.relative_volume:
        score += min(25, max(0, focus.relative_volume - 1) * 18)
    if focus and focus.volume_spike:
        score += 15
    return _bounded(score)


def _catalysts(watch: IntelligenceWatchlistSymbol, focus: FocusGroupAnalysis | None, prediction: WeeklyPrediction | None) -> list[str]:
    catalysts = []
    if focus:
        catalysts.append(focus.key_catalyst)
    if prediction and prediction.key_drivers:
        catalysts.extend(prediction.key_drivers[:2])
    catalysts.append(f"Theme exposure: {', '.join((watch.themes or [])[:3])}")
    return list(dict.fromkeys([item for item in catalysts if item]))[:4]


def _risks(focus: FocusGroupAnalysis | None, result: ScanResult | None, prediction: WeeklyPrediction | None) -> list[str]:
    risks = []
    if result:
        risks.extend(result.risk_flags or [])
    if focus and focus.risk_level == "high":
        risks.append("High focus-group risk level")
    if prediction and prediction.main_risks:
        risks.extend(prediction.main_risks[:2])
    return list(dict.fromkeys(risks or ["Normal market and execution risk"]))[:4]


def _action(conviction: float, asymmetric: float, risk: float, bias: str) -> str:
    if risk >= 75:
        return "Watch only; require confirmation and smaller position sizing."
    if bias == "bullish" and conviction >= 70 and asymmetric >= 65:
        return "High-priority research candidate; validate catalyst and risk/reward."
    if conviction >= 60:
        return "Monitor for entry-zone confirmation."
    return "Keep on watchlist; wait for stronger evidence."


def _theme_trends(watchlist: list[IntelligenceWatchlistSymbol], opportunities: list[dict]) -> list[dict]:
    symbols_by_theme: dict[str, list[str]] = defaultdict(list)
    score_by_symbol = {item["symbol"]: item["conviction_score"] for item in opportunities}
    for row in watchlist:
        for theme in row.themes or ["uncategorized"]:
            symbols_by_theme[theme].append(row.symbol)
    trends = []
    for theme, symbols in symbols_by_theme.items():
        avg = sum(score_by_symbol.get(symbol, 50) for symbol in symbols) / len(symbols)
        leaders = sorted(symbols, key=lambda symbol: score_by_symbol.get(symbol, 0), reverse=True)[:3]
        trends.append(
            {
                "theme": theme,
                "strength": round(avg, 1),
                "symbol_count": len(symbols),
                "leaders": leaders,
                "summary": f"{theme} strength is {avg:.0f}/100 across {len(symbols)} tracked names.",
            }
        )
    return sorted(trends, key=lambda item: item["strength"], reverse=True)[:10]


def _simulate_scenarios(opportunities: list[dict]) -> list[dict]:
    leaders = [item["symbol"] for item in opportunities if item["conviction_score"] >= 65][:4]
    fragile = [item["symbol"] for item in opportunities if item["risk_score"] >= 65][:4]
    quantum = [item["symbol"] for item in opportunities if item["symbol"] in {"IONQ", "RGTI"}]
    return [
        {
            "scenario": "AI data-center capex acceleration",
            "probability": 0.34,
            "expected_reaction": "Momentum and long-term investors bid compute, memory, power, and server infrastructure leaders.",
            "vulnerable_symbols": fragile,
            "likely_beneficiaries": leaders,
            "confidence_adjustment": 0.08,
            "risk_adjustment": 0.03,
            "agent_consensus": {
                "institutional_investors": "accumulate leaders",
                "momentum_traders": "chase breakouts",
                "retail_traders": "rotate toward familiar AI names",
                "macro_investors": "watch rates and power constraints",
            },
        },
        {
            "scenario": "Semiconductor supply-chain or margin shock",
            "probability": 0.22,
            "expected_reaction": "News-driven traders de-risk expensive hardware names; value and cash-flow quality matter more.",
            "vulnerable_symbols": fragile or [item["symbol"] for item in opportunities[:3]],
            "likely_beneficiaries": [item["symbol"] for item in opportunities if item["risk_score"] < 45][:3],
            "confidence_adjustment": -0.06,
            "risk_adjustment": 0.12,
            "agent_consensus": {
                "hedge_funds": "short weakest balance sheets",
                "panic_sellers": "pressure high-volatility names",
                "long_term_investors": "wait for valuation reset",
                "news_driven_traders": "react to guidance revisions",
            },
        },
        {
            "scenario": "Quantum or advanced-computing narrative surge",
            "probability": 0.18,
            "expected_reaction": "Speculative capital flows into quantum names, with high reversal risk after sharp moves.",
            "vulnerable_symbols": quantum,
            "likely_beneficiaries": quantum,
            "confidence_adjustment": 0.03,
            "risk_adjustment": 0.15,
            "agent_consensus": {
                "retail_traders": "amplify narrative",
                "social_media_influencers": "increase attention",
                "institutional_investors": "remain selective",
                "risk_management": "reduce size into volatility",
            },
        },
    ]


def _prediction_accuracy(db: Session) -> dict:
    report = db.query(WeeklyEvaluationReport).order_by(WeeklyEvaluationReport.created_at.desc()).first()
    if not report:
        return {
            "status": "collecting",
            "accuracy": None,
            "evaluated_count": 0,
            "false_positives": 0,
            "notes": "No completed weekly evaluation yet.",
        }
    return {
        "status": "active",
        "accuracy": report.accuracy,
        "evaluated_count": report.evaluated_count,
        "false_positives": report.false_positives,
        "notes": report.confidence_notes,
    }


def _risk_overview(opportunities: list[dict], simulations: list[dict]) -> dict:
    fragile = [item["symbol"] for item in opportunities if item["risk_score"] >= 65]
    high_conviction = [item for item in opportunities if item["conviction_score"] >= 70]
    avg_risk = sum(item["risk_score"] for item in opportunities) / len(opportunities) if opportunities else 0
    return {
        "regime": "risk-on" if high_conviction and avg_risk < 55 else "selective" if avg_risk < 70 else "defensive",
        "portfolio_concentration": "high AI infrastructure concentration; enforce position limits before execution",
        "crowded_trade_risk": "elevated" if len(high_conviction) >= 4 else "moderate",
        "fragile_setups": fragile[:6],
        "notes": [
            "Simulation output is advisory and separated from trade execution.",
            "Manual approval remains required before any broker workflow.",
            f"Average opportunity risk score is {avg_risk:.0f}/100.",
        ],
    }


def _next_actions(opportunities: list[dict], simulations: list[dict]) -> list[str]:
    actions = ["Run the morning scanner before market open and regenerate focus-group analysis."]
    if opportunities:
        top = opportunities[0]
        actions.append(f"Review {top['symbol']} first: {top['action']}")
    if any(result["risk_adjustment"] >= 0.12 for result in simulations):
        actions.append("Check fragile setups before sizing any momentum trade.")
    actions.append("Evaluate weekly predictions after Friday close to update learning weights.")
    return actions
