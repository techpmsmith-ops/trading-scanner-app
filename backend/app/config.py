import os

from dotenv import load_dotenv


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "development").lower()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_scanner.db")
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "yfinance")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
SCAN_DEFAULT_LOOKBACK_DAYS = int(os.getenv("SCAN_DEFAULT_LOOKBACK_DAYS", "300"))
MIN_AVG_VOLUME = int(os.getenv("MIN_AVG_VOLUME", "500000"))
MAX_ATR_PERCENT = float(os.getenv("MAX_ATR_PERCENT", "8"))
YFINANCE_CACHE_DIR = os.getenv("YFINANCE_CACHE_DIR", "./.yf_cache")
MARKET_DATA_FALLBACK_PROVIDER = os.getenv("MARKET_DATA_FALLBACK_PROVIDER", "stooq")
PHASE2_PREDICTION_SYMBOLS = [
    item.strip().upper()
    for item in os.getenv("PHASE2_PREDICTION_SYMBOLS", "INTC,NVDA,AMD,IONQ,NVTS,RVI,SMCI,RGTI,RKLB,MU").split(",")
    if item.strip()
]
FOCUS_GROUP_SYMBOLS = [
    item.strip().upper()
    for item in os.getenv("FOCUS_GROUP_SYMBOLS", ",".join(PHASE2_PREDICTION_SYMBOLS)).split(",")
    if item.strip()
]
KRONOS_ENABLED = os.getenv("KRONOS_ENABLED", "false").lower() == "true"
KRONOS_MODEL_NAME = os.getenv("KRONOS_MODEL_NAME", "NeoQuasar/Kronos-mini")
KRONOS_TOKENIZER_NAME = os.getenv("KRONOS_TOKENIZER_NAME", "NeoQuasar/Kronos-Tokenizer-2k")
KRONOS_DEVICE = os.getenv("KRONOS_DEVICE", "auto")
KRONOS_LOOKBACK_BARS = int(os.getenv("KRONOS_LOOKBACK_BARS", "120"))
KRONOS_FORECAST_BARS = int(os.getenv("KRONOS_FORECAST_BARS", "5"))
KRONOS_MAX_SYMBOLS_PER_RUN = int(os.getenv("KRONOS_MAX_SYMBOLS_PER_RUN", "10"))
KRONOS_TIMEOUT_SECONDS = int(os.getenv("KRONOS_TIMEOUT_SECONDS", "60"))
KRONOS_BULLISH_THRESHOLD_PCT = float(os.getenv("KRONOS_BULLISH_THRESHOLD_PCT", "1.5"))
KRONOS_BEARISH_THRESHOLD_PCT = float(os.getenv("KRONOS_BEARISH_THRESHOLD_PCT", "-1.5"))
KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT = float(os.getenv("KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT", "5.0"))
KRONOS_WEIGHT = float(os.getenv("KRONOS_WEIGHT", "0.20"))
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

DEFAULT_TICKER_METADATA = {
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "asset_type": "etf", "description": "ETF tracking large-cap U.S. stocks in the S&P 500."},
    "QQQ": {"name": "Invesco QQQ Trust", "asset_type": "etf", "description": "ETF tracking the Nasdaq-100, with heavy technology exposure."},
    "IWM": {"name": "iShares Russell 2000 ETF", "asset_type": "etf", "description": "ETF tracking small-cap U.S. stocks in the Russell 2000."},
    "DIA": {"name": "SPDR Dow Jones Industrial Average ETF Trust", "asset_type": "etf", "description": "ETF tracking the Dow Jones Industrial Average."},
    "AAPL": {"name": "Apple", "asset_type": "stock", "description": "Consumer technology company focused on iPhone, Mac, services, and devices."},
    "MSFT": {"name": "Microsoft", "asset_type": "stock", "description": "Software, cloud, AI, gaming, and enterprise technology company."},
    "NVDA": {"name": "NVIDIA", "asset_type": "stock", "description": "AI accelerator, GPU, data-center, networking, and software platform leader."},
    "AMZN": {"name": "Amazon", "asset_type": "stock", "description": "E-commerce, cloud infrastructure, advertising, logistics, and digital services company."},
    "META": {"name": "Meta Platforms", "asset_type": "stock", "description": "Social media, advertising, messaging, AI, and metaverse technology company."},
    "GOOGL": {"name": "Alphabet", "asset_type": "stock", "description": "Search, advertising, YouTube, cloud, Android, and AI technology company."},
    "TSLA": {"name": "Tesla", "asset_type": "stock", "description": "Electric vehicle, energy storage, autonomy, and robotics company."},
    "AMD": {"name": "Advanced Micro Devices", "asset_type": "stock", "description": "CPU, GPU, AI accelerator, embedded, and data-center semiconductor company."},
    "NFLX": {"name": "Netflix", "asset_type": "stock", "description": "Global streaming entertainment and advertising-supported media company."},
    "JPM": {"name": "JPMorgan Chase", "asset_type": "stock", "description": "Large U.S. bank with consumer, investment banking, markets, and asset management businesses."},
    "BAC": {"name": "Bank of America", "asset_type": "stock", "description": "Large U.S. bank with consumer banking, wealth, markets, and lending businesses."},
    "XOM": {"name": "Exxon Mobil", "asset_type": "stock", "description": "Integrated oil and gas company with upstream, refining, chemicals, and low-carbon projects."},
    "CVX": {"name": "Chevron", "asset_type": "stock", "description": "Integrated oil and gas company with global upstream and downstream operations."},
    "UNH": {"name": "UnitedHealth Group", "asset_type": "stock", "description": "Healthcare insurance, services, pharmacy benefits, and health technology company."},
    "COST": {"name": "Costco Wholesale", "asset_type": "stock", "description": "Membership warehouse retailer focused on bulk consumer goods and recurring membership revenue."},
    "AVGO": {"name": "Broadcom", "asset_type": "stock", "description": "Semiconductor and infrastructure software company with AI networking and custom silicon exposure."},
    "SMCI": {"name": "Super Micro Computer", "asset_type": "stock", "description": "AI server, rack-scale data-center, storage, and liquid-cooling hardware company."},
    "PLTR": {"name": "Palantir Technologies", "asset_type": "stock", "description": "Data analytics, AI platform, government, and commercial software company."},
    "INTC": {"name": "Intel", "asset_type": "stock", "description": "CPU, foundry, AI PC, data-center, and semiconductor manufacturing company."},
    "IONQ": {"name": "IonQ", "asset_type": "stock", "description": "Quantum computing company developing trapped-ion quantum systems and cloud access."},
    "NVTS": {"name": "Navitas Semiconductor", "asset_type": "stock", "description": "Power semiconductor company focused on GaN and SiC chips for efficient power systems."},
    "RVI": {"name": "Retail Value Inc.", "asset_type": "stock", "description": "Special situation monitor slot retained from the AI infrastructure watchlist."},
    "RGTI": {"name": "Rigetti Computing", "asset_type": "stock", "description": "Quantum computing company developing superconducting quantum processors and systems."},
    "RKLB": {"name": "Rocket Lab", "asset_type": "stock", "description": "Space launch, satellite systems, defense, and space infrastructure company."},
    "MU": {"name": "Micron Technology", "asset_type": "stock", "description": "Memory and storage semiconductor company with DRAM, NAND, and HBM exposure."},
}

SETUP_DISCLAIMER = (
    "This is a scanner-generated setup for review, not a trade recommendation. "
    "Confirm risk, liquidity, market conditions, and your own trading plan before acting."
)
