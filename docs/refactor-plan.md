# Buffotte Backend Refactor Plan

Date: 2026-04-29

## Execution Log

- 2026-04-29: Started Phase 0/1.
  - Added `app/` package skeleton.
  - Added central `app/core/config.py` for CORS and selected runtime settings.
  - Extracted `GET /api/system/stats` into `app/routers/system.py` while preserving the public route.
  - Added a local-development fallback for system stats when `/proc` is unavailable.
  - Moved core table bootstrap out of module import and into FastAPI lifespan startup.
  - Added route registration smoke tests in `tests/test_api_contract.py`.
  - Updated `pyproject.toml` package list to include `app` and `models`.
- 2026-04-29: Continued router extraction.
  - Added shared dependency providers in `app/dependencies.py`.
  - Extracted `POST /api/register` and `POST /api/login` into `app/routers/auth.py`.
  - Extracted `GET /api/user/profile` and `GET /api/user/details/{email}` into `app/routers/users.py`.
  - Added `app/schemas/auth.py` for auth request models.
  - Kept public route paths stable and expanded route registration tests.
- 2026-04-29: Extracted BuffTracker integration.
  - Added `app/integrations/bufftracker.py` as the single owner of BuffTracker URL construction.
  - Extracted the public `/api/bufftracker/{path:path}` proxy into `app/routers/bufftracker.py`.
  - Reused `BuffTrackerClient` from item K-line refresh paths and CS2 base item sync.
  - Added URL construction unit tests for Docker service URLs and self-proxy URLs.

## Goal

Reduce coupling around `api.py`, make the backend easier to extend, and improve runtime reliability without breaking the existing frontend or Docker API contract.

The first rule for this refactor is compatibility: keep current public routes such as `/api/login`, `/api/kline/chart-data`, `/api/bufftracker/{path:path}`, `/api/item/kline-data/{market_hash_name}`, `/api/track/add`, and `/api/profit/*` working while internals move behind clearer boundaries.

## Current Findings

`api.py` is currently 1121 lines and acts as all of these at once:

- FastAPI app construction and middleware setup.
- CORS and global exception handling.
- Startup side effects such as `user_manager.create_user_table()`.
- Request/response schemas.
- User auth, K-line, news, summary, buff-tracker proxy, item price, tracking, skin, system stats, and profit routes.
- Direct SQL query execution and response serialization.
- External HTTP proxying and URL construction.
- Background task orchestration.
- Shell command execution for refresh workflows.

The largest coupling risks are:

- Database configuration is duplicated across many modules via repeated `load_dotenv()` and `os.getenv(...)`.
- Table creation and schema patching happen inside processors, module import paths, request paths, and scripts.
- Many synchronous PyMySQL calls run inside `async def` routes, sometimes without `run_in_executor`.
- Route handlers mix HTTP concerns, SQL, external API calls, business rules, and serialization.
- `BUFFTRACKER_URL` path handling is duplicated in `api.py` and `db/item_kline_processor.py`.
- `frontend/src/services/api.js` centralizes some calls, but several views still use direct `fetch("/api/...")`.
- There are no obvious tests in the repository, so route movement needs contract tests before deeper rewrites.
- `Dockerfile.backend` installs dependencies manually rather than from one canonical dependency source.

## Non-Goals For The First Pass

- Do not change public API paths or response shapes.
- Do not change frontend request base URLs as part of backend modularization.
- Do not change `.env` values or expose secret values in documentation.
- Do not replace MySQL, PyMySQL, Vue, or FastAPI.
- Do not rewrite all processors at once.
- Do not introduce a large framework layer that hides the current business logic.

## Target Architecture

Proposed backend layout:

```text
app/
  main.py                  # create_app(), middleware, router registration
  core/
    config.py              # typed Settings from environment
    logging.py             # logging setup
    errors.py              # exception handlers and error mapping
    lifecycle.py           # startup/shutdown tasks
  db/
    connection.py          # shared PyMySQL connection factory
    migrations.py          # explicit schema bootstrap helpers
  dependencies.py          # FastAPI dependency providers
  schemas/
    auth.py
    tracking.py
    kline.py
    items.py
    profit.py
  routers/
    auth.py
    users.py
    kline.py
    news.py
    summary.py
    bufftracker.py
    items.py
    tracking.py
    skins.py
    system.py
    profit.py
  services/
    auth_service.py
    kline_service.py
    item_kline_service.py
    news_service.py
    tracking_service.py
    profit_service.py
    system_service.py
  repositories/
    users.py
    kline.py
    news.py
    tracking.py
    skins.py
    profit.py
  integrations/
    bufftracker.py         # URL building + HTTP client wrapper
  jobs/
    kline_refresh.py
    profit_prediction.py
api.py                    # compatibility shim: from app.main import app
```

Existing `db/`, `crawler/`, `models/`, and `llm/` modules can remain in place while the new `app/` layer wraps them. The first migration should move route code and configuration boundaries, not force an immediate rewrite of every data processor.

## Router Split

Move current `api.py` route groups into routers with stable prefixes:

| Router | Existing routes |
| --- | --- |
| `routers.auth` | `POST /api/register`, `POST /api/login` |
| `routers.users` | `GET /api/user/profile`, `GET /api/user/details/{email}` |
| `routers.kline` | `/api/kline/chart-data`, `/api/kline/refresh`, `/api/kline/latest`, `/api/kline/market-analysis` |
| `routers.summary` | `GET /api/summary/latest` |
| `routers.news` | `GET /api/news`, `GET /api/news/stats` |
| `routers.bufftracker` | `/api/bufftracker/{path:path}` |
| `routers.items` | `/api/item-price/*`, `/api/item/kline-*` |
| `routers.tracking` | `/api/track/add`, `/api/track/list/{email}`, `/api/track/remove` |
| `routers.skins` | `/api/skin/trending`, `/api/skin/search`, `/api/skin/{skin_id}/detail` |
| `routers.system` | `GET /api/system/stats` |
| `routers.profit` | `/api/profit/platform-fees`, `/api/profit/calculate`, `/api/profit/calculate-all`, `/api/profit/predict/{market_hash_name}`, `/api/profit/tracked/{email}` |

Keep route decorators exactly equivalent during the first extraction. This lets the frontend remain untouched.

## Refactor Phases

### Phase 0: Safety Rails

Create route contract tests before moving behavior:

- Add `tests/test_api_contract.py` using `fastapi.testclient.TestClient`.
- Test route registration and simple mocked happy paths.
- Add import smoke test: `from api import app`.
- Mock database processors and external clients so tests do not require MySQL, buff-tracker, or LLM keys.
- Capture current response envelopes for high-value endpoints:
  - `/api/system/stats`
  - `/api/kline/latest`
  - `/api/news`
  - `/api/bufftracker/search`
  - `/api/track/list/{email}`
  - `/api/profit/calculate`

Acceptance criteria:

- Test suite can run without a live database.
- `api.py` can still be imported in the same way Uvicorn imports it today.
- No route path changes.

### Phase 1: App Factory And Configuration

Introduce `app/main.py` and keep `api.py` as a thin shim:

```python
from app.main import app
```

Move these concerns into `app/main.py`:

- FastAPI app construction.
- Wiki mounting.
- Middleware registration.
- Exception handlers.
- Router registration.

Create `app/core/config.py` with a single settings object. Prefer Pydantic settings if adding `pydantic-settings` is acceptable; otherwise use a small typed dataclass around `os.getenv`.

Settings should include:

- Database host, port, user, password, database, charset.
- CORS origins.
- `BUFFTRACKER_URL`.
- LLM provider/model keys.
- Runtime flags such as local/dev/production.

Acceptance criteria:

- Only one module owns environment parsing for the HTTP app.
- `.env` values are not logged.
- Docker behavior remains unchanged.

### Phase 2: Extract Routers Without Rewriting Business Logic

Move route functions into `app/routers/*`.

Use dependency providers for current global processors:

- `get_user_manager()`
- `get_kline_processor()`
- `get_item_kline_processor()`
- `get_user_actions()`
- `get_profit_processor()`
- `get_item_crawler()`

At this phase, it is acceptable for routers to call the existing `db/*` processors directly. The objective is to reduce `api.py` size safely, not to perfect the domain model in one step.

Acceptance criteria:

- `api.py` is below 20 lines.
- Each router file has one clear domain.
- Existing frontend pages continue using the same URLs.
- `npm run build` still passes.

### Phase 3: Services And Repositories

Move business logic out of routers:

- Routers validate HTTP input and map exceptions to responses.
- Services implement workflows.
- Repositories own SQL reads/writes.
- Integrations own external HTTP calls.

High-priority service extractions:

- `BuffTrackerClient`: builds `/api/...` versus `/api/bufftracker/...` paths in one place.
- `ItemKlineService`: cache freshness, fetch, parse, store, and background refresh.
- `KlineService`: chart data, latest row, market analysis.
- `NewsService`: latest summary, news listing, stats.
- `ProfitService`: prediction + platform profit calculation.
- `AuthService`: register, login, user details.

Acceptance criteria:

- Routers contain minimal business logic.
- Duplicate `BUFFTRACKER_URL` handling is removed.
- Direct SQL in routers is removed.

### Phase 4: Database Lifecycle

Centralize database concerns:

- `app/db/connection.py` provides one connection factory.
- Processors receive database settings or a connection factory instead of reading environment directly.
- Table creation moves into explicit startup/bootstrap functions.
- Startup must not make the whole app unavailable if non-critical tables fail, but it should log failures clearly.
- Long-term: replace ad hoc `CREATE TABLE` and `ALTER TABLE` scattered through processors with explicit migration scripts.

Immediate risk to address:

- `user_manager.create_user_table()` currently runs during module import and can prevent app startup if the database is down.
- `ensure_profit_tables` swallows errors silently. This should become a logged, bounded startup task or a health-check-visible degraded state.

Acceptance criteria:

- Importing the app does not require a live database.
- Database failures are observable in logs and health checks.
- Repeated request handling does not repeatedly attempt schema changes unless explicitly needed.

### Phase 5: Async Boundaries And Background Work

Make blocking work explicit:

- Wrap remaining PyMySQL calls in threadpool helpers until a future async database library is chosen.
- Move `subprocess.run(["python", "-m", "db.kline_data_processor"])` out of request handlers or gate it behind a background job interface.
- Track background tasks started by `asyncio.create_task` so failures are logged.
- Add timeouts and response normalization for external HTTP calls.

Potential future shape:

- Lightweight in-process background task abstraction first.
- Later, if needed, a separate worker container for crawlers, predictions, and scheduled jobs.

Acceptance criteria:

- Async routes do not block the event loop with expensive synchronous work.
- Background task exceptions are not lost.
- Refresh endpoints return predictable status for queued/running/failed work.

### Phase 6: Frontend API Cleanup

Do this only after backend route extraction is stable.

- Keep `client = axios.create({ baseURL: "/api" })`.
- Move direct `fetch("/api/...")` in views into `frontend/src/services/api.js`.
- Keep `/api/bufftracker` proxy path intact.
- Add one place for request timeout and error normalization.
- Avoid reintroducing `VITE_API_BASE_URL` unless there is a clear deployment need, because Nginx already proxies `/api/`.

Acceptance criteria:

- Vue views do not hand-build API URLs except for external links.
- API error display is consistent across pages.

### Phase 7: Tests, Tooling, And Documentation

Add a practical quality floor:

- Backend unit tests for services with mocked repositories.
- API contract tests for all routers.
- Integration tests behind an opt-in flag for live MySQL/buff-tracker.
- Frontend build check.
- Document local/Docker/production environment modes.
- Add `.env.example` or update docs so required keys are explicit without secrets.
- Align `pyproject.toml`, `poetry.lock`, and `Dockerfile.backend` dependency sources.

Acceptance criteria:

- A new developer can run a test suite without production secrets.
- Docker deployment instructions match current compose networking.
- API docs reflect current routes, including profit endpoints.

## Suggested First Implementation Sequence

1. Add contract tests and app import smoke test.
2. Add `app/core/config.py` and `app/main.py`, keep `api.py` as a shim.
3. Extract middleware and exception handlers.
4. Extract `auth`, `users`, and `system` routers first. These are small and good confidence builders.
5. Extract `bufftracker` router and create `BuffTrackerClient`. This directly reduces the risk around Docker URL confusion.
6. Extract `items` and `tracking` routers.
7. Extract `kline`, `news`, `summary`, `skins`, and `profit`.
8. Move direct SQL out of routers into services/repositories.
9. Move table creation to lifecycle/bootstrap.
10. Consolidate frontend API service calls.

## Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Route path changes break frontend | High | Contract tests before route extraction; keep decorators identical |
| Database unavailable during app import | High | Move schema setup out of import path |
| buff-tracker Docker name/network mismatch | High | Centralize `BUFFTRACKER_URL` resolution and document compose network mode |
| Long predictions block API workers | Medium | Run prediction in executor now, job queue later |
| Silent schema/bootstrap failures | Medium | Log failures and expose health/degraded status |
| Secrets leak through logs/docs | High | Never log raw settings; keep `.env` ignored; provide redacted examples |
| Large refactor creates merge conflicts with current feature work | Medium | Extract routers one domain at a time; do not move unrelated frontend code in same PR |

## Success Criteria

- `api.py` is a small compatibility entrypoint.
- Backend domains are discoverable by folder and router name.
- The public API contract is unchanged.
- App import and tests do not require a live database.
- Database configuration has a single owner.
- buff-tracker URL construction has a single owner.
- Existing Docker and frontend behavior can be validated with a short checklist.

## Validation Checklist For Each Phase

- `python -m compileall app api.py db crawler models llm`
- Backend import smoke test passes.
- API contract tests pass.
- `npm run build` from `frontend/` passes.
- Docker compose config still includes required networks and env files.
- Manual smoke routes:
  - `GET /api/system/stats`
  - `POST /api/login`
  - `GET /api/kline/latest`
  - `GET /api/bufftracker/search?name=ak`
  - `GET /api/track/list/{email}`

## Notes On Current Dirty Worktree

The current working tree already includes feature work for profit prediction, item prediction, tracking UI, Docker network edits, and the sidebar GSAP fix. Refactor work should avoid reverting or mixing those changes. If this plan is implemented, do it in small commits so feature changes and structural changes remain reviewable.
