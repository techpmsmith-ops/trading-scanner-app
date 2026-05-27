# Progress Handoff

## Kronos Focus Integration - 2026-05-27

Kronos is now integrated as a bounded Focus Group forecasting signal, not a scanner-wide trade decision engine.

Current production posture:

- Kronos defaults to enabled.
- Kronos only runs for `FOCUS_GROUP_SYMBOLS`.
- Kronos is capped at `KRONOS_MAX_SYMBOLS_PER_RUN=5`.
- Kronos score remains bounded by `KRONOS_WEIGHT=0.20`.
- Render env vars were added by the user.
- Render migration `20260526_0010_kronos_integration.py` has been applied successfully.
- Render backend rebuilt successfully with PyTorch/Kronos runtime dependencies installed.

Key commits pushed:

```text
776bbd5 Harden Kronos local enablement
bc32eba Enable Kronos for focus group by default
9888794 Fix Kronos migration boolean backfill
856060b Show Kronos forecast on focus pages
c6061fb Add Kronos runtime dependencies
5750025 Use scanner Kronos data on focus pages
```

Important fixes completed:

- Fixed Postgres boolean backfill in the Kronos Alembic migration.
- Added Kronos runtime dependencies to backend requirements:
  - `torch`
  - `einops`
  - `huggingface_hub`
  - `safetensors`
  - `tqdm`
- Added `.env` loading through `python-dotenv`, so local env files now work as documented.
- Added Focus page Kronos panel.
- Added Focus page fallback to use linked scanner-result Kronos data when the stored Focus analysis has stale/unavailable Kronos output.
- Updated shared frontend `dateTime(...)` formatting to display `America/New_York` with timezone abbreviation. In May this displays `EDT`; in winter it will display `EST`.

Validation completed locally:

```text
python -m alembic downgrade 20260525_0009
python -m alembic upgrade head
=> passed

python -m pytest app/tests/test_phase2.py app/tests/test_kronos.py
=> 17 passed

python -m pytest
=> 38 passed

npm.cmd run build
=> passed
```

Hosted observations:

- `/scanner/MU` showed Kronos fields correctly after the backend started producing Kronos scan output.
- `/focus/MU` initially showed stale Focus-analysis Kronos data; this was patched so Focus pages can fall back to fresh scanner Kronos data.
- Old persisted Focus rows may still contain prior unavailable/error payloads until refreshed or until the new fallback deploy is live.

Next verification steps:

1. Confirm Render has deployed commit `5750025` or newer.
2. Confirm Vercel has deployed commit `5750025` or newer.
3. Run a fresh scan.
4. Open `/scanner/MU` and confirm Kronos shows bias/confidence/model.
5. Open `/focus/MU` and confirm the Kronos Forecast panel matches the scanner Kronos output.
6. Confirm last scan timestamps display Eastern time with timezone abbreviation.

If Render becomes slow or unstable due to PyTorch size/memory:

```text
KRONOS_ENABLED=false
```

No migration rollback is required for that safety switch.

## Tech Debt Backlog - 2026-05-25

Backend tests are passing, but pytest currently emits non-blocking deprecation warnings that should be cleaned up during production hardening:

- Migrate FastAPI startup/shutdown hooks in `backend/app/main.py` from `@app.on_event(...)` to a lifespan handler.
- Replace naive `datetime.utcnow()` usage with timezone-aware UTC timestamps, reviewing SQLAlchemy/Pydantic serialization before changing persisted timestamp behavior.
- Leave the Starlette `python_multipart` warning alone unless dependency upgrades make it actionable; it is emitted by a dependency import path, not app code.

Current verification after installing dependencies into the bundled Python 3.12 runtime:

```text
PYTHONPATH=backend python -m pytest backend/app/tests
=> 22 passed
```

## Local Intelligence Testing Handoff - 2026-05-25

The AI Infrastructure Market Intelligence work is implemented locally and the user confirmed they could log in and reach `/intelligence`.

Added locally:

- Backend `/intelligence/dashboard` and `/intelligence/watchlist` routes.
- Dynamic `intelligence_watchlist_symbols` table and Alembic migration:
  - `backend/alembic/versions/20260525_0007_market_intelligence.py`
- Seeded Focus Group / AI infrastructure watchlist:
  - `INTC`, `NVDA`, `AMD`, `IONQ`, `NVTS`, `RVI`, `SMCI`, `RGTI`, `RKLB`, `MU`
- New service:
  - `backend/app/services/intelligence.py`
- New frontend page:
  - `frontend/app/intelligence/page.tsx`
- Nav link:
  - `Intelligence`
- Previous chart percentage labels are still included in the working tree.

Local testing state:

```text
Backend: http://127.0.0.1:8000
Frontend: http://localhost:3000
Intelligence page: http://localhost:3000/intelligence
```

Local DB migration was applied:

```powershell
cd backend
$env:PYTHONPATH="."
C:\Users\techp\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m alembic upgrade head
```

Backend dependency install/testing used the bundled Python 3.12 runtime because the default Python 3.13 could not install the pinned pandas wheel cleanly:

```powershell
C:\Users\techp\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r backend\requirements.txt
$env:PYTHONPATH='backend'
C:\Users\techp\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\app\tests
```

Result:

```text
22 passed
```

Local admin account was created because `backend/trading_scanner.db` had no users.

Important: the temporary local password was exposed during local testing. Do not reuse it for hosted/production. Replace it before any deployment or shared testing.

Runtime note:

- A stale/hung Next dev process on port `3000` briefly caused `ERR_CONNECTION_REFUSED` / hanging requests.
- Windows denied termination of PID `2240`, but the existing dev server eventually responded and redirected `/intelligence` to login.
- If this recurs, restart the machine or manually stop the stale Node/Next process, then start fresh:

```powershell
cd backend
$env:PYTHONPATH="."
C:\Users\techp\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --reload

cd frontend
npm.cmd run dev
```

## Latest Hosted Deployment Handoff - 2026-05-16

We started the first real hosted deployment flow using:

- Database: Neon PostgreSQL
- Backend: Render
- Frontend: Vercel

The user provided:

```text
Old backend URL checked earlier: https://trading-scanner-backend.onrender.com/
Active Render backend URL: https://trading-scanner-app-g1d7.onrender.com/
Frontend URL provided: https://vercel.com/techpmsmith-8934s-projects/trading-scanner-app
Public frontend URL: https://trading-scanner-app.vercel.app/
Admin email originally discussed: techpsmith@gmail.com
Correct admin email: techpmsmith@gmail.com
```

Important security note: the user pasted an admin password into chat. Treat that password as exposed. Rotate it before production use and do not store it in repo docs or chat.

### Hosted Backend Check

Initial network check against the old Render backend showed that the domain was reachable, but it was not serving this Stage 1 MVP backend.

Observed:

```text
GET https://trading-scanner-backend.onrender.com/
=> {"status":"Trading Scanner API Running","version":"1.0.0"}

GET https://trading-scanner-backend.onrender.com/health
=> 404 Not Found
```

The hosted OpenAPI document exposed routes like:

```text
/trade
/bot/toggle
/account
/market/{symbol}
/strategies
/backtest/{symbol}
```

Those are not the Stage 1 scanner/journal MVP routes. The expected MVP backend should expose:

```text
/health
/auth/login
/scan/latest
/scan/status
/scan/runs
/journal
/performance/summary
```

Update on 2026-05-17: a corrected Render service deployed successfully at:

```text
https://trading-scanner-app-g1d7.onrender.com/
```

Health check passed:

```text
GET https://trading-scanner-app-g1d7.onrender.com/health
=> {"status":"ok","service":"trading-scanner-api"}
```

Update after Vercel/Render redeploy:

```text
GET https://trading-scanner-app-g1d7.onrender.com/health
=> 200

GET https://trading-scanner-app-g1d7.onrender.com/scan/latest without token
=> 401

GET https://trading-scanner-app.vercel.app/
=> 200
```

Remaining hosted smoke-test steps require the rotated private admin password and should be run locally by the user, not pasted into chat.

### Ticker Detail Production Error

After login and scan, clicking a ticker showed a Vercel production Server Components render error. Local inspection found the dynamic route was using synchronous `params.symbol` while Next.js 16 expects dynamic route `params` to be awaited. The route was patched:

```text
frontend/app/scanner/[symbol]/page.tsx
```

Changes:

- `params` is now typed as `Promise<{ symbol: string }>` and awaited.
- `/data/{symbol}` fetch failures are handled gracefully.
- If price history is unavailable, the ticker detail page shows a caution message instead of crashing.

Local frontend build passed after the patch:

```text
npm run build
=> passed
```

Next step: commit/push this frontend fix and redeploy Vercel.

### Chart Enhancements Added Locally

The frontend now includes additional visual representations:

- Scanner page:
  - Top 10 score bar chart
  - Setup mix donut chart
- Ticker detail page:
  - Score breakdown bar chart
  - Existing price chart remains, with a graceful fallback if price history is unavailable
- Performance page:
  - Equity curve from closed journal trades with P&L
  - Trade outcome bar chart
  - Existing mistake frequency chart remains

New files:

```text
frontend/components/ScannerCharts.tsx
frontend/components/TickerScoreChart.tsx
frontend/components/PerformanceCharts.tsx
```

Updated files:

```text
frontend/app/scanner/page.tsx
frontend/app/scanner/[symbol]/page.tsx
frontend/app/performance/page.tsx
frontend/lib/api.ts
```

Local validation:

```text
npm run build
=> passed
```

These chart changes need to be committed/pushed to GitHub before Vercel can deploy them.

### Phase 2 Local Implementation - 2026-05-18

Implemented Phase 2 decision-support features locally:

- `/signals` frontend page with:
  - Daily top-five watchlist candidates
  - Weekly prediction tracking table
  - Feedback weight display
  - Admin action buttons for top-five generation, weekly prediction generation, and feedback evaluation
- Backend `/phase2` API:
  - `GET /phase2/dashboard`
  - `POST /phase2/recommendations/generate`
  - `GET /phase2/recommendations/latest`
  - `POST /phase2/predictions/generate`
  - `POST /phase2/predictions/evaluate`
  - `GET /phase2/predictions`
  - `GET /phase2/weights/latest`
  - alert subscription/test endpoints
- New persisted models:
  - `DailyRecommendation`
  - `WeeklyPrediction`
  - `ScoringWeight`
  - `AlertSubscription`
- Alembic migration:
  - `backend/alembic/versions/20260518_0003_phase2.py`
- Optional alert integrations:
  - Telegram via `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
  - SMS via Twilio env vars
- Market-data fallback:
  - yfinance remains primary
  - Stooq fallback added through `MARKET_DATA_FALLBACK_PROVIDER=stooq`
- Weekly tracked symbols:
  - `INTC`, `NVDA`, `AMD`, `IONQ`, `NVTS`
- Feedback loop:
  - Evaluates completed weekly predictions against actual weekly return when price bars exist
  - Nudges scanner component weights within bounded `0.8x` to `1.2x`
  - Future scanner runs apply latest scoring weights

Validation:

```text
backend alembic upgrade head => passed
backend pytest => 13 passed
frontend npm run build => passed
```

Deployment reminder:

```bash
cd backend
alembic upgrade head
```

Run this on Render after pushing/deploying Phase 2 so Neon has the new tables.

### Phase 2 Hosted Status - 2026-05-18

Phase 2 was pushed and deployed.

Key commits:

```text
4f3140f Add phase 2 signals and prediction tracking
92c2b78 Log auth failures safely
```

Hosted checks:

```text
GET https://trading-scanner-app-g1d7.onrender.com/health
=> 200

GET https://trading-scanner-app-g1d7.onrender.com/phase2/dashboard without token
=> 401

GET https://trading-scanner-app.vercel.app/signals
=> 200
```

OpenAPI confirmed Phase 2 routes are live:

```text
/phase2/dashboard
/phase2/recommendations/generate
/phase2/recommendations/latest
/phase2/predictions/generate
/phase2/predictions/evaluate
/phase2/predictions
/phase2/weights/latest
/phase2/alerts
/phase2/alerts/{alert_id}
/phase2/alerts/test/{channel}
```

Auth issue encountered:

- `/auth/login` briefly returned `500`.
- Added safer auth exception logging.
- After redeploy, PowerShell login check returned `200`.
- The pasted output included a live JWT token. Rotate `JWT_SECRET_KEY` in Render after testing.

Signals UI current state:

- `/signals` loads successfully after login.
- Daily Top Five section shows empty state.
- Weekly Prediction Tracking section shows empty state.
- Feedback weights show defaults active.

Next resume steps:

1. Run a fresh scanner run from Dashboard.
2. Return to Signals.
3. Click **Top Five**.
4. Click **Weekly Predictions**.
5. Confirm daily top five and weekly predictions populate.
6. Do not use **Evaluate Feedback** until a tracked week has completed and price data exists.
7. Rotate Render `JWT_SECRET_KEY`, redeploy backend, then log out and back in.

### Weekly Feedback Upgrade - 2026-05-23

Implemented a richer end-of-week prediction evaluation flow locally:

- Market week now ends Friday instead of Sunday.
- Evaluation can run on Saturday for the just-ended trading week.
- Evaluation fetches missing tracked-symbol price bars before comparing actual performance.
- Weekly predictions now store:
  - false-positive flag
  - news sentiment score
  - news sentiment label
- Added `WeeklyEvaluationReport` persisted report with:
  - prediction accuracy
  - wins/losses
  - win/loss ratio
  - false positives
  - indicator effectiveness
  - news sentiment correlation
  - SPY/QQQ market conditions
  - scoring weight changes
  - confidence calibration notes
- Signals page now displays the latest weekly evaluation report.
- Scoring weight adjustment now uses hit rate and false positives by component, still bounded between `0.8x` and `1.2x`.

Deployment reminder:

```bash
cd backend
alembic upgrade head
```

The new migration is:

```text
backend/alembic/versions/20260523_0004_weekly_evaluation_reports.py
```

### Prediction Outcome Reasons - 2026-05-24

Added explicit outcome reasons for weekly prediction evaluation:

- `weekly_predictions.outcome_reason`
- Signals table shows a **Reason** column beside outcome
- Neutral hits/misses now explain the +/-1% neutral band
- Bullish/bearish hits/misses explain whether actual weekly return aligned with direction

New migration:

```text
backend/alembic/versions/20260524_0005_prediction_outcome_reason.py
```

### Render Fix Needed

In Render, open `trading-scanner-backend` and verify:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Also set this Render environment variable before redeploying:

```text
PYTHON_VERSION=3.12.13
```

Why: the first Render build on 2026-05-17 used Render's default Python `3.14.3`. `pandas==2.2.2` did not install from a ready wheel there and started a long source build during `Preparing metadata (pyproject.toml)`. The app was locally validated on Python `3.12.13`, so Render should be pinned to that version.

The repo now includes `.python-version` files at both the repo root and `backend/`, but the Render environment variable is the quickest explicit fix.

Also confirm Render is connected to the correct GitHub repo and branch containing this MVP code.

After redeploy, this must pass:

```text
GET https://trading-scanner-backend.onrender.com/health
```

Expected:

```json
{"status":"ok","service":"trading-scanner-api"}
```

Then run in Render Shell:

```bash
alembic upgrade head
python -m app.cli create-admin --email techpmsmith@gmail.com --password "NEW-PRIVATE-PASSWORD"
```

Use a new private password because the previous one was exposed in chat.

### Vercel Fix Needed

The public Vercel frontend URL is:

```text
https://trading-scanner-app.vercel.app/
```

Update Render:

```text
ALLOWED_ORIGINS=https://trading-scanner-app.vercel.app
```

Then redeploy the Render backend.

### Next Resume Steps

1. Update Render `ALLOWED_ORIGINS` to `https://trading-scanner-app.vercel.app`.
2. Confirm Render env vars are production-safe:

```text
APP_ENV=production
DEBUG=false
DATABASE_URL=<Neon URL entered only in Render>
AUTO_CREATE_TABLES=false
MARKET_DATA_PROVIDER=yfinance
SCAN_DEFAULT_LOOKBACK_DAYS=300
MIN_AVG_VOLUME=500000
MAX_ATR_PERCENT=8
YFINANCE_CACHE_DIR=./.yf_cache
JWT_SECRET_KEY=<long secret entered only in Render>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720
ALLOWED_ORIGINS=<public Vercel URL>
```

5. Run hosted smoke test:

```powershell
cd "C:\Users\gwatk\OneDrive\Documents\Develop trading App\trading-scanner-app\scripts"
python deployment_smoke_test.py `
  --backend-url "https://trading-scanner-app-g1d7.onrender.com" `
  --frontend-url "https://trading-scanner-app.vercel.app" `
  --email "techpmsmith@gmail.com" `
  --password "NEW-PRIVATE-PASSWORD"
```

6. Run one hosted production scan from the UI.
7. Confirm scan history, scan status, scanner results, journal create/edit/close, and performance summary.

## Current State

The Stage 1 AI Trading Scanner MVP has been scaffolded and validated at local MVP build level.

## Completed

- FastAPI backend with SQLAlchemy models and SQLite default persistence
- Seeded default stock/ETF universe
- yfinance market data ingestion
- Daily OHLCV price bar persistence with duplicate protection
- Rule-based indicator calculations
- Setup classification
- Transparent 0-100 scoring model
- Risk/reward estimate generation
- Deterministic scanner explanations and disclaimers
- Scan run history with partial-success failure handling
- Ticker API
- Market data API
- Scanner API
- Journal CRUD API
- Performance summary API
- Next.js frontend with:
  - Dashboard
  - Scanner results table
  - Ticker detail page with chart
  - Add-to-journal flow
  - Journal page and detail editor
  - Performance page
- README with local setup instructions
- Backend tests for scanner logic, API health, journal CRUD, mock scanner run, indicators, scoring, setup classification, risk/reward, and missing-data handling

## Validation Performed

Backend:

```text
pytest
10 passed
```

Frontend:

```text
npm install
npm run build
Next production build succeeded
```

## Latest Smoke Test

- Created `backend/.venv` and installed backend requirements into it.
- Started FastAPI with uvicorn on `127.0.0.1:8000`.
- Confirmed `GET /health` returned OK.
- Started Next dev server on `127.0.0.1:3000`.
- Ran a real yfinance-backed scan after upgrading yfinance and setting a writable yfinance cache directory.
- Confirmed latest scan saved 22/22 ticker results.
- Confirmed frontend routes returned 200 for dashboard, scanner, ticker detail, journal, journal detail, and performance.
- Created a scan-linked journal entry, edited it, closed it, and confirmed performance summary updated.
- Final validation:
  - Backend `pytest`: 10 passed.
  - Frontend `npm audit`: 0 vulnerabilities.
  - Frontend `npm run build`: passed on Next.js 16.2.6.

## Private Deployment Prep Added

- Alembic migration setup with an initial schema migration.
- PostgreSQL-ready `DATABASE_URL` support.
- Simple JWT email/password auth for private deployment.
- Admin creation command: `python -m app.cli create-admin --email you@example.com --password "..."`
- Protected backend API routers.
- Protected frontend routes with login page and cookie token forwarding.
- Dockerfiles for backend and frontend.
- `docker-compose.yml` with backend, frontend, and PostgreSQL.
- GitHub Actions CI for backend pytest and frontend build.
- Scanner concurrency guard to prevent overlapping runs.
- README migration, Docker, deployment, and backup notes.

Note: In this PowerShell session, `npm run build` needed `C:\Program Files\nodejs` prepended to PATH so npm shims resolved the correct Node executable.

## Important Fixes Made During Validation

- Registered `sample_bars` as a pytest fixture.
- Updated API tests to use `TestClient(app)` as a context manager so FastAPI startup creates tables.
- Removed unused frontend `eslint` and `eslint-config-next` dev dependencies because install failed on a Windows permission issue in an optional resolver postinstall path.
- Upgraded `yfinance` to `0.2.66` and configured a writable project-local yfinance cache directory.
- Hardened the frontend API client to trim API base URLs and safely join request paths.
- Added loading/error boundaries and clearer scan failure/no-result messages.
- Upgraded Next.js to `16.2.6` and added a PostCSS override to clear npm audit.

## Known Gaps Before Production Deployment

- No hosted deployment config yet.
- No Dockerfile or CI pipeline yet.
- No PostgreSQL migration setup yet.
- No auth yet, intentionally deferred for Stage 1.
- In-app browser automation was blocked by a local `AppData` permission error, so UI verification was done through route-level HTTP checks plus live API workflow checks.

## Suggested Next Session

1. Run backend and frontend locally together.
2. Execute one real scanner run against yfinance data.
3. Click through dashboard, scanner table, ticker detail, add-to-journal, journal edit, and performance.
4. Upgrade Next.js to a patched version and rebuild.
5. Add deployment pieces: Docker or platform config, PostgreSQL config, migrations, and basic auth.
