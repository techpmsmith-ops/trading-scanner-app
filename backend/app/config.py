import os


APP_ENV = os.getenv("APP_ENV", "development").lower()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_scanner.db")
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "yfinance")
SCAN_DEFAULT_LOOKBACK_DAYS = int(os.getenv("SCAN_DEFAULT_LOOKBACK_DAYS", "300"))
MIN_AVG_VOLUME = int(os.getenv("MIN_AVG_VOLUME", "500000"))
MAX_ATR_PERCENT = float(os.getenv("MAX_ATR_PERCENT", "8"))
YFINANCE_CACHE_DIR = os.getenv("YFINANCE_CACHE_DIR", "./.yf_cache")
MARKET_DATA_FALLBACK_PROVIDER = os.getenv("MARKET_DATA_FALLBACK_PROVIDER", "stooq")
PHASE2_PREDICTION_SYMBOLS = [
    item.strip().upper()
    for item in os.getenv("PHASE2_PREDICTION_SYMBOLS", "INTC,NVDA,AMD,IONQ,NVTS").split(",")
    if item.strip()
]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-before-deploying")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]


def validate_runtime_config() -> None:
    if APP_ENV == "production":
        if DEBUG:
            raise RuntimeError("DEBUG must be false in production")
        if JWT_SECRET_KEY in {"", "change-me-before-deploying"} or len(JWT_SECRET_KEY) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be set to a strong secret in production")
        if not os.getenv("ALLOWED_ORIGINS"):
            raise RuntimeError("ALLOWED_ORIGINS must be explicitly set in production")
        if AUTO_CREATE_TABLES:
            raise RuntimeError("AUTO_CREATE_TABLES must be false in production; run Alembic migrations instead")
        if DATABASE_URL.startswith("sqlite"):
            raise RuntimeError("Production DATABASE_URL must use PostgreSQL, not SQLite")

DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "TSLA", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "UNH",
    "COST", "AVGO", "SMCI", "PLTR",
]

SETUP_DISCLAIMER = (
    "This is a scanner-generated setup for review, not a trade recommendation. "
    "Confirm risk, liquidity, market conditions, and your own trading plan before acting."
)
