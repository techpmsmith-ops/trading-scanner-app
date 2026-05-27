# AI Trading Scanner MVP

Stage 1 MVP for an AI-assisted trading scanner. The app scans a configurable stock/ETF universe with daily candles, calculates transparent technical indicators, scores potential setups, shows ranked watchlist candidates, and supports trade journaling plus basic performance review.

This is a decision-support tool. It does not place trades.

## What It Does

- Fetches end-of-day OHLCV data with `yfinance`
- Stores tickers, price bars, scan runs, scan results, and journal entries locally
- Calculates EMA/SMA trend, RSI, MACD, ATR, volume, and market-structure indicators
- Classifies Stage 1 setup types with deterministic rules
- Scores each ticker from 0 to 100 with visible score components
- Estimates entry zone, stop, targets, and risk/reward with simple rules
- Provides a dashboard, scanner table, ticker detail page, journal, and performance page
- Provides a backtesting lab for comparing transparent strategy profiles against historical bars
- Handles per-ticker scanner failures without crashing the whole run
- Optionally adds Kronos AI forecasts as a bounded scoring signal for Focus Group stocks

## What It Does Not Do

- Broker execution or live trading
- Autonomous trading
- Options, crypto, futures, or forex strategies
- Social sentiment analysis
- AI-generated trade calls
- Kronos-only buy/sell decisions
- Backtests that predict future results
- Real-time or high-frequency scanning

## Project Structure

```text
trading-scanner-app/
  backend/
    app/
      main.py
      database.py
      models.py
      schemas.py
      api/
      services/
      tests/
    requirements.txt
    .env.example
  frontend/
    app/
    components/
    lib/
    package.json
    .env.example
```

## Backend Setup

```bash
cd trading-scanner-app/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.cli create-admin --email you@example.com --password "choose-a-strong-password"
uvicorn app.main:app --reload --reload-dir app --reload-dir alembic
```

The API runs at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend Setup

```bash
cd trading-scanner-app/frontend
npm install
copy .env.example .env.local
npm run dev
```

The UI runs at `http://localhost:3000`.

## Run Tests

```bash
cd trading-scanner-app/backend
pytest
```

## Database Migrations

Local development uses SQLite by default:

```text
DATABASE_URL=sqlite:///./trading_scanner.db
AUTO_CREATE_TABLES=true
```

Production should use PostgreSQL:

```text
DATABASE_URL=postgresql://user:password@host:5432/trading_scanner
AUTO_CREATE_TABLES=false
```

Apply migrations:

```bash
cd trading-scanner-app/backend
alembic upgrade head
```

Create a future migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Create the first private admin user:

```bash
python -m app.cli create-admin --email you@example.com --password "choose-a-strong-password"
```

## Configure The Ticker Universe

The default universe is seeded on backend startup:

```text
SPY, QQQ, IWM, DIA, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, NFLX, JPM, BAC, XOM, CVX, UNH, COST, AVGO, SMCI, PLTR
```

You can edit the universe through the ticker API:

```bash
curl -X POST http://localhost:8000/tickers ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\":\"XLK\",\"asset_type\":\"etf\",\"active\":true}"
```

To deactivate a ticker:

```bash
curl -X DELETE http://localhost:8000/tickers/XLK
```

## Run A Scan Manually

From the UI, click **Run Scanner** on the dashboard.

From the API:

```bash
curl -X POST http://localhost:8000/scan/run
```

The backend also schedules a daily end-of-day scan at 6:00 PM America/New_York while the API process is running.

## Key API Routes

- `GET /health`
- `GET /tickers`
- `POST /tickers`
- `PATCH /tickers/{symbol}`
- `DELETE /tickers/{symbol}`
- `POST /data/refresh`
- `GET /data/{symbol}`
- `POST /scan/run`
- `GET /scan/runs`
- `GET /scan/runs/{id}`
- `GET /scan/status`
- `GET /scan/latest`
- `GET /scan/results/{id}`
- `GET /journal`
- `POST /journal`
- `GET /journal/{id}`
- `PATCH /journal/{id}`
- `DELETE /journal/{id}`
- `GET /performance/summary`
- `GET /phase2/dashboard`
- `POST /phase2/focus/generate`
- `GET /phase2/focus/latest`
- `GET /phase2/focus/{symbol}/explanation-context`
- `POST /phase2/focus/{symbol}/explain`
- `POST /phase2/morning-pipeline`
- `POST /phase2/recommendations/generate`
- `GET /phase2/recommendations/latest`
- `POST /phase2/predictions/generate`
- `POST /phase2/predictions/regenerate-current-week`
- `POST /phase2/predictions/evaluate`
- `GET /phase2/predictions`
- `GET /phase2/weights/latest`
- `GET /phase2/alerts`
- `POST /phase2/alerts`
- `POST /backtests/run`
- `GET /backtests/strategies`

## Backtesting Lab

The Backtests page runs historical research against stored or freshly downloaded OHLCV data. It supports:

- Daily, weekly, and monthly timeframe testing
- Rule-based strategy comparisons: trend following, momentum strength, breakout, mean reversion, and AI-assisted composite
- Risk-adjusted metrics including Sharpe ratio, annualized volatility, maximum drawdown, win rate, average trade return, profit factor, and final equity
- Strategy-vs-benchmark equity curve visualization
- Recent trade review for each strategy profile

Backtests are stateless and do not place trades or save orders. The AI-assisted composite is a transparent scanner-style indicator vote, not a black-box prediction engine.

## Configuration

Backend `.env`:

```text
APP_ENV=development
DEBUG=false
DATABASE_URL=sqlite:///./trading_scanner.db
AUTO_CREATE_TABLES=true
MARKET_DATA_PROVIDER=yfinance
POLYGON_API_KEY=
MARKET_DATA_FALLBACK_PROVIDER=stooq
SCAN_DEFAULT_LOOKBACK_DAYS=300
MIN_AVG_VOLUME=500000
MAX_ATR_PERCENT=8
YFINANCE_CACHE_DIR=./.yf_cache
PHASE2_PREDICTION_SYMBOLS=INTC,NVDA,AMD,IONQ,NVTS,RVI,SMCI,RGTI,RKLB,MU
FOCUS_GROUP_SYMBOLS=INTC,NVDA,AMD,IONQ,NVTS,RVI,SMCI,RGTI,RKLB,MU
KRONOS_ENABLED=false
KRONOS_MODEL_NAME=NeoQuasar/Kronos-mini
KRONOS_TOKENIZER_NAME=NeoQuasar/Kronos-Tokenizer-2k
KRONOS_DEVICE=auto
KRONOS_LOOKBACK_BARS=120
KRONOS_FORECAST_BARS=5
KRONOS_MAX_SYMBOLS_PER_RUN=10
KRONOS_TIMEOUT_SECONDS=60
KRONOS_BULLISH_THRESHOLD_PCT=1.5
KRONOS_BEARISH_THRESHOLD_PCT=-1.5
KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT=5.0
KRONOS_WEIGHT=0.20
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_TO_NUMBER=
JWT_SECRET_KEY=change-me-before-deploying
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Frontend `.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
API_INTERNAL_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

## Deployment Preparation

The MVP is structured for deployment but is not deployed yet.

Recommended production shape:

- Backend: run FastAPI with `uvicorn` or `gunicorn` behind a managed HTTPS proxy.
- Database: use PostgreSQL by setting `DATABASE_URL` to a PostgreSQL connection string.
- Frontend: build with `npm run build` and run with `npm start`, or deploy to a Next.js-compatible host.
- Environment: copy `backend/.env.example` and `frontend/.env.example` into platform-specific secret/config settings.
- Scheduler: keep the backend process alive so the APScheduler daily scan can run, or move scheduled scans to a managed cron worker.

Pre-deployment checklist:

- Run `pytest` from `backend/`.
- Run `npm run build` from `frontend/`.
- Perform a real scan against the deployed backend.
- Confirm CORS allows the deployed frontend origin.
- Add authentication before exposing personal journal data publicly.
- Add database migrations before moving beyond local SQLite.

## First Hosted Deployment Checklist

Required backend environment variables:

```text
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:password@host:5432/trading_scanner
AUTO_CREATE_TABLES=false
MARKET_DATA_PROVIDER=yfinance
SCAN_DEFAULT_LOOKBACK_DAYS=300
MIN_AVG_VOLUME=500000
MAX_ATR_PERCENT=8
YFINANCE_CACHE_DIR=./.yf_cache
JWT_SECRET_KEY=<at-least-32-random-characters>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720
ALLOWED_ORIGINS=https://your-frontend-domain.example
```

Required frontend environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.example
API_INTERNAL_BASE_URL=https://your-backend-domain.example
NEXT_PUBLIC_APP_ENV=production
```

Recommended beginner-friendly hosted stack:

- Frontend: Vercel
- Backend: Render Web Service or Railway Web Service
- Database: Neon PostgreSQL or Supabase PostgreSQL

Suggested order:

1. Create the managed PostgreSQL database first.
2. Deploy the backend and point it at PostgreSQL.
3. Run Alembic migrations against the hosted database.
4. Create the first admin user.
5. Deploy the frontend and point it at the hosted backend.
6. Run the deployment smoke test.

PostgreSQL setup:

- Create a private PostgreSQL database.
- Create a database user with ownership or migration rights for the app database.
- Store the connection string as `DATABASE_URL`.
- Enable managed automated backups before first real use.

Neon PostgreSQL notes:

- Create a Neon project and database.
- Copy the pooled or direct connection string into the backend `DATABASE_URL`.
- Keep SSL enabled if Neon includes it in the connection string.
- Enable automated backups or point-in-time restore for the project tier you choose.

Supabase PostgreSQL notes:

- Create a Supabase project.
- Use the Postgres connection string from Project Settings.
- Keep database credentials private and never place `DATABASE_URL` in frontend environment variables.
- Review backup settings before storing real journal history.

Backend deploy steps:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Render backend steps:

- Create a new Web Service from the repository.
- Root directory: `backend`.
- Build command: `pip install -r requirements.txt`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Add the backend environment variables in Render's Environment tab.
- After the first deploy, open Render Shell and run `alembic upgrade head`.

Railway backend steps:

- Create a new service from the repository.
- Set the service root to `backend`.
- Add the backend environment variables in Railway Variables.
- Use start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Run `alembic upgrade head` from a Railway shell or one-off command.

Admin user creation:

```bash
python -m app.cli create-admin --email you@example.com --password "choose-a-strong-password"
```

For hosted services, run the same command in the provider shell after migrations complete.

Frontend deploy steps:

```bash
npm ci
npm run build
npm start
```

Vercel frontend steps:

- Import the repository into Vercel.
- Set the root directory to `frontend`.
- Add `NEXT_PUBLIC_API_BASE_URL`, `API_INTERNAL_BASE_URL`, and `NEXT_PUBLIC_APP_ENV`.
- Deploy.
- Copy the Vercel URL into backend `ALLOWED_ORIGINS`.
- Redeploy the backend after changing `ALLOWED_ORIGINS`.

Post-deploy smoke test:

```bash
python scripts/deployment_smoke_test.py \
  --backend-url https://your-backend-domain.example \
  --frontend-url https://your-frontend-domain.example \
  --email you@example.com \
  --password "choose-a-strong-password"
```

Manual smoke test:

- Confirm backend `/health` returns OK.
- Confirm unauthenticated `/scan/latest` returns 401.
- Confirm login works.
- Confirm dashboard loads after login.
- Run one scan.
- Open `/scanner/runs` and confirm completed, partial, and failed runs are visible.
- Open scanner results and a ticker detail page.
- Add a result to the journal.
- Close a test journal entry and confirm performance updates.

Production config guardrails:

- `APP_ENV=production` refuses placeholder or short `JWT_SECRET_KEY` values.
- `APP_ENV=production` requires explicit `ALLOWED_ORIGINS`.
- `APP_ENV=production` refuses `AUTO_CREATE_TABLES=true`.
- `APP_ENV=production` refuses SQLite.
- `DEBUG=true` is rejected in production.

Secure cookie guidance:

- The current frontend stores the JWT in a same-site browser cookie for a simple private deployment.
- In production over HTTPS, the frontend marks the cookie `Secure`.
- Host the app only behind HTTPS.
- Prefer a future HTTP-only secure cookie/session proxy before exposing the app beyond a private trusted user.
- Keep `ACCESS_TOKEN_EXPIRE_MINUTES` reasonably short for hosted use.

Operational notes:

- Scanner execution is restricted to authenticated admin users.
- Concurrent scanner runs are rejected so a manual scan cannot overlap the scheduled scan.
- Scan history is retained; new scans do not overwrite older scan runs.
- yfinance failures are retried with short backoff and then logged per ticker.
- Review `/scanner/runs` after a hosted scan to spot partial data-provider failures.

## Docker Compose Preview

Docker support is included for private deployment preparation:

```bash
cd trading-scanner-app
docker compose build
docker compose up
```

Then create the first admin user inside the backend container:

```bash
docker compose exec backend python -m app.cli create-admin --email you@example.com --password "choose-a-strong-password"
```

The compose stack includes:

- `postgres`
- `backend`
- `frontend`

Before hosting, replace all example secrets in `backend/.env.docker.example`, especially `JWT_SECRET_KEY` and the PostgreSQL password.

### Docker Validation On Windows

1. Install Docker Desktop for Windows.
2. Start Docker Desktop and wait until the engine is running.
3. From PowerShell:

```powershell
cd "C:\Users\gwatk\OneDrive\Documents\Develop trading App\trading-scanner-app"
docker compose build
docker compose up
```

4. In a second PowerShell window, run migrations if you did not use the compose command that runs them:

```powershell
docker compose exec backend alembic upgrade head
```

5. Create the admin user:

```powershell
docker compose exec backend python -m app.cli create-admin --email you@example.com --password "choose-a-strong-password"
```

6. Verify locally:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Login with the admin user.
- Run one scan and review scanner, journal, and performance pages.

## Backup Note

For SQLite local development, back up `backend/trading_scanner.db` when the app is stopped.

For PostgreSQL production, prefer managed automated backups. Also know the manual commands.

Manual backup:

```bash
pg_dump "$DATABASE_URL" > trading_scanner_backup.sql
```

Manual restore into a fresh database:

```bash
psql "$DATABASE_URL" < trading_scanner_backup.sql
```

For compressed custom-format backups:

```bash
pg_dump -Fc "$DATABASE_URL" > trading_scanner_backup.dump
pg_restore --clean --if-exists --dbname "$DATABASE_URL" trading_scanner_backup.dump
```

Keep backups encrypted, restrict access, and test restores before relying on them.

## Phase 2 Features

Phase 2 adds richer decision-support features while keeping the app private and non-executing:

- Interactive ticker price chart periods: `1M`, `3M`, `YTD`, `1Y`, and `All`.
- Secondary market-data fallback through Stooq when yfinance fails.
- Daily top-five watchlist candidates generated from the latest scan.
- Weekly prediction tracking for `INTC`, `NVDA`, `AMD`, `IONQ`, and `NVTS`.
- Tiered intelligence model:
  - Tier 1 Focus Group Watchlist: `INTC`, `NVDA`, `AMD`, `IONQ`, `NVTS`, `RVI`, `SMCI`, `RGTI`, `RKLB`, and `MU`.
  - Tier 2 weekly prediction engine for each Focus Group stock.
  - Tier 3 feedback loop that stores stock-specific behavior profiles and adjusts future component weights.
  - Tier 4 broader market discovery that surfaces only exceptional high-confidence scanner candidates when available.
- Daily Focus Group summaries with bias, confidence, technical setup, catalyst, risk level, watch action, price zones, support/resistance, relevance tags, and news sentiment.
- Premarket pipeline scheduled for 7:00 AM America/New_York. After the scan completes, it generates Focus Group analysis, broader discovery top-five rows, and daily alert delivery.
- Dedicated Focus Group stock pages at `/focus/{symbol}` with charts, technical context, prediction history, accuracy profile, scoring transparency, and a grounded explanation assistant.
- Feedback loop that evaluates completed weekly predictions against actual weekly price movement and nudges scanner component weights within a bounded `0.8x` to `1.2x` range.
- End-of-week evaluation reports showing prediction accuracy, win/loss ratio, false positives, indicator effectiveness, news-sentiment alignment, and SPY/QQQ market conditions.
- Optional Telegram and SMS alerts for top-five and weekly prediction summaries.

## Optional Kronos Forecasting

Kronos is an open-source foundation model for financial K-line/OHLCV sequences. In this app it is a modular forecasting layer, not a replacement scanner and not a final trade decision engine. When enabled, Kronos runs first against the Focus Group symbols and contributes a capped signal to the scanner score.

Kronos is checked out under `external/Kronos`. The lightweight default is:

```text
KRONOS_MODEL_NAME=NeoQuasar/Kronos-mini
KRONOS_TOKENIZER_NAME=NeoQuasar/Kronos-Tokenizer-2k
```

Install and verify locally:

```bash
python scripts/setup_kronos.py
```

If packages are already installed and you only want to verify model loading:

```bash
python scripts/setup_kronos.py --skip-install
```

Turn Kronos on:

```text
KRONOS_ENABLED=true
KRONOS_DEVICE=auto
```

Turn it off:

```text
KRONOS_ENABLED=false
```

Run a test forecast through the protected internal API:

```bash
curl -X POST http://localhost:8000/api/kronos/forecast \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"NVDA\",\"fetch_from_polygon\":true,\"forecast_bars\":5}"
```

Health check:

```bash
curl http://localhost:8000/api/kronos/health -H "Authorization: Bearer <token>"
```

Example scan result fields:

```json
{
  "kronos_enabled": true,
  "kronos_model_name": "NeoQuasar/Kronos-mini",
  "kronos_bias": "bullish",
  "kronos_confidence": 72,
  "kronos_expected_range_low": 101.25,
  "kronos_expected_range_high": 108.4,
  "kronos_volatility_estimate": 4.8,
  "kronos_summary": "Kronos NeoQuasar/Kronos-mini projects a bullish 5-bar path.",
  "kronos_error": null
}
```

Kronos scoring is intentionally capped. If Kronos is disabled or unavailable, the existing technical, volume, risk, setup-quality, news, sentiment, confidence, and trade-plan logic continues to run without it.

Hardware expectations: `Kronos-mini` is the practical local-development starting point. CPU can work for smoke tests but may be slow; CUDA is preferred for repeated inference. Upgrade to `NeoQuasar/Kronos-base` only after validating latency and memory.

Evaluate completed Kronos predictions:

```bash
python scripts/evaluate_kronos_predictions.py
```

Limitations: Kronos is research forecasting, not guaranteed financial advice. Forecast quality depends on clean OHLCV data, model fit for the symbol/timeframe, market regime, and local hardware. Keep position sizing and final trade decisions outside Kronos.

These outputs are still scanner-generated signals for review, not trade recommendations.

Apply Phase 2 migrations:

```bash
cd trading-scanner-app/backend
alembic upgrade head
```

Focus Group symbols are configurable:

```text
FOCUS_GROUP_SYMBOLS=INTC,NVDA,AMD,IONQ,NVTS,RVI,SMCI,RGTI,RKLB,MU
PHASE2_PREDICTION_SYMBOLS=INTC,NVDA,AMD,IONQ,NVTS,RVI,SMCI,RGTI,RKLB,MU
```

Optional Telegram alert env vars:

```text
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<chat id>
```

Optional Twilio SMS env vars:

```text
TWILIO_ACCOUNT_SID=<account sid>
TWILIO_AUTH_TOKEN=<auth token>
TWILIO_FROM_NUMBER=<twilio number>
TWILIO_TO_NUMBER=<destination number>
```

## Disclaimer

This software is for educational and journaling purposes only. Scanner-generated setups are not trade recommendations and are not financial advice. Confirm risk, liquidity, market conditions, and your own trading plan before acting.
"# trading-scanner-app" 
"# trading-scanner-app" 
"# trading-scanner-app" 
"# trading-scanner-app" 
