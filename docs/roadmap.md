# Roadmap

ColdChain AI is built in vertical slices. Each phase delivers a complete,
tested feature spanning domain → application → infrastructure → API →
frontend, and ends with all quality gates green.

## Phase guide

| Phase | Title | Status |
| ----- | ----- | ------ |
| 1 | Foundation: skeleton, CI-ready tooling, health feature | ✅ Complete |
| 2 | Core domain & entities: warehouses, PHCs, shipments, logistics (drivers, vehicles, containers), routes, waypoints | ✅ Complete |
| 3 | Authentication, RBAC and user management (JWT, refresh tokens, permission catalog) | ✅ Complete |
| 4 | Facilities, logistics and shipments management services + APIs | ✅ Complete |
| 5.1 | Weather service with OpenWeather provider, caching and mock fallback | ✅ Complete |
| 5.2 | Alerting: cold-chain alert lifecycle (raise, list, acknowledge, resolve) | ✅ Complete |
| 5.3 | Operations dashboard (stat cards, charts, live queries) | ✅ Complete |
| 5.4 | **Temperature excursion prediction engine** (rule-based, explainable, RBAC-protected) | ✅ **Complete** |
| 6 | Route recommendation engine (planned) | 🔜 Next |
| 7 | Real-time telemetry ingestion & live tracking | ⏳ Future |
| 8 | ML model swap behind the scoring ports | ⏳ Future |

## Phase 5.4 — Temperature Excursion Prediction Engine (complete)

**Objective.** Predict the risk of a vaccine temperature excursion before
dispatch, using a transparent, explainable rule engine so operators can see
*why* a shipment is risky.

**Delivered.**

- Pure scoring function `score_excursion_risk` with per-rule contributions and
  risk bounded to `[0, 1]` (`app/services/intelligence_service.py`).
- `PredictionRules` dataclass with configurable weights/thresholds, hydrated
  from `PREDICTION_*` settings (`app/core/config.py`).
- Real route geometry (warehouse → PHC haversine distance) and live weather at
  the destination; confidence reflects the weather source (0.90 live vs 0.60
  mock).
- Container safe-band awareness when a container is assigned.
- Persistence via `PredictionRepository`; GET (latest) + POST (compute) under
  `Permission.PREDICTION_VIEW` / `Permission.PREDICTION_MANAGE`.
- Value objects `TemperatureReading`, `GeoCoordinate`, `ExcursionReport`
  (frozen dataclasses with validation).
- Frontend dashboard widgets: Temperature Trend envelope + Prediction Risk
  distribution charts.
- Unit tests for scoring, haversine and the prediction workflow (33 backend
  tests passing); frontend lint + typecheck green.

## Phase 6 — Route Recommendation Engine (next)

Phase 6 delivers the second core AI feature from the project tagline:
**"recommends the safest delivery route"**. It mirrors the Phase 5.4 pattern
(rule engine + persistence + RBAC + frontend) applied to routing.

### Goal

Given a shipment (origin warehouse → destination PHC), score one or more
candidate routes by safety, persist them, and let an operator select the best
one — with the same transparency the prediction engine provides.

### Current state (gap analysis)

- `IntelligenceService.plan_route` exists but is a stub: it uses **hard-coded
  placeholder coordinates**, returns a transient `WarmRoute`, and is never
  persisted. `intelligence.route_router` is **defined but not registered** in
  `app/api/routes/__init__.py`.
- Full route CRUD + lifecycle already exists and is registered
  (`/routes`): create, get, update, optimize, select, status transitions,
  soft-delete, waypoint CRUD — all RBAC-protected and persisted.
- `RouteAlternatives` schema exists but is unused; `ROUTE_PLAN` /
  `ROUTE_SELECT` permissions exist.

### Scope (backend)

1. **Route rules engine** — `RouteRules` dataclass + pure
   `score_route_safety(...)` returning `(safety_score, features,
   explanations)` with per-rule contributions (distance/duration, weather
   factor from live weather, stop count, priority), mirroring
   `score_excursion_risk`. Safety bounded to `[0, 1]` and mapped to the
   `safety_score` field (`Route.validate_metrics` allows 0–100).
2. **Real geometry** — resolve origin from `WarehouseRepository` and
   destination from `PhCentreRepository` (no more placeholder coordinates);
   fall back to sensible defaults only when a facility is missing.
3. **Alternatives** — generate N candidate routes (e.g. shortest vs. safest
   vs. balanced) and return them via `RouteAlternatives` (`selected` +
   `alternatives`).
4. **Persistence** — persist the planned route + waypoints through
   `RouteRepository` / `WaypointRepository` so plans survive restarts and
   appear in the dashboard's existing `useRoutes` feed.
5. **Routing** — register `intelligence.route_router` in
   `app/api/routes/__init__.py`; guard GET with `ROUTE_VIEW` and plan/select
   with `ROUTE_PLAN` / `ROUTE_SELECT`.
6. **Settings** — add `ROUTE_*` settings (weights, max stops, default
   speeds, weather-impact knobs) alongside the `PREDICTION_*` block.

### Scope (frontend)

7. **Routes page** at `/routes` (nav item already exists in the sidebar):
   list planned routes with safety scores, weather factor and alternatives;
   "Plan route" action and "Select" action per candidate.
8. **Dashboard route widget** — safety-score distribution / average safety
   stat reusing `ChartCard` + `PageState` patterns.
9. Feature folder `frontend/features/routes/` with typed DTOs in
   `frontend/lib/types` (already has `RouteRead`, `WaypointRead`).

### Tests & quality

10. Unit tests for `score_route_safety` (bounds, rule contributions, priority
    boost), route planning workflow, alternatives generation, persistence.
11. API tests for the registered route endpoints incl. RBAC.
12. Quality gates: backend `pytest -q`, `ruff check app tests`, `mypy app`;
    frontend `npm run quality`; E2E curl of plan/select/GET flows.

### Definition of done

- `POST /api/v1/shipments/{id}/route` (or equivalent) returns a persisted,
  explainable route with real coordinates and live weather factor.
- `GET .../route` returns the selected route + alternatives; select is
  idempotent (one selected route per shipment).
- Frontend routes page + dashboard widget render; all quality gates green;
  docs updated.
