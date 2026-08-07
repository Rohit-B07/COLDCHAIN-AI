# Architecture

## Design goals

The foundation must support a prototype today and a nationwide healthcare
platform later. Decisions are therefore biased toward:

- **Testability** — business logic is framework-free and tested in isolation.
- **Maintainability** — dependencies point inward; layers never leak.
- **Scalability** — services are stateless and horizontally scalable behind
  the database and message bus (added later).
- **Security** — secrets via environment, non-root containers, CORS hardening.

## Layering (backend)

The backend follows Clean Architecture with a hexagonal flavor (ports &
adapters).

```
API layer          app/api          HTTP concerns only (routers, DI, DTOs)
   |
Application layer  app/use_cases, app/services   business workflows
   |
Domain layer       app/domain      pure entities, value objects, ports
   |
Infrastructure     app/models, app/repositories, app/db   persistence, engines
```

### Dependency rule

> Source code dependencies only point **inward**. Nothing in an inner circle
> may know about an outer circle.

- `app.domain` imports **nothing** from FastAPI, SQLAlchemy, or Pydantic.
- `app.use_cases` depends on `app.domain` interfaces (protocols), never on
  concrete repositories.
- `app.api` composes concrete implementations and injects them via FastAPI
  `Depends` (see `app/api/deps/container.py`).
- The **health feature** is the reference pattern for every future feature.

### Mapping flow for a request

```
Route (app/api/routes)                      # HTTP + validation
  -> DI container (app/api/deps)            # injects implementation
  -> Use case (app/use_cases)               # orchestrates business action
  -> Repository port (app/domain/repositories)   # interface only
  -> Concrete repo (app/repositories)       # SQLAlchemy
  -> DB session (app/db)
```

### Why not one big model file / MVC?

| Approach | Trade-off |
| -------- | --------- |
| **MVC (models + routes only)** | Fast to build, but business logic couples to framework & DB; untestable without a database; hard to replace DB or framework. |
| **Clean Architecture (chosen)** | Slightly more upfront structure; each layer independently testable and swappable; clear ownership. Ideal for a platform expected to grow. |

## Frontend architecture

- **App Router** with route groups; the public section lives under
  `app/(public)`.
- **Feature-scoped modules** (`features/`) encapsulate each capability
  (components, hooks, API calls) and expose a public barrel. This is a
  "folder-based" variant of Domain-Driven Design (D2C).
- **Shared building blocks** live in `components/ui` (shadcn/ui) and
  `lib` (config, typed API client, utilities).
- **Environment config** is centralised in `lib/config.ts`; components never
  read `process.env` directly.

### Frontend data flow

```
Component (features/<feature>) -> hooks (state/polling)
  -> apiClient (lib/api/client.ts) -> fetch -> typed domain types (lib/types)
```

The API client and config are the only places that know about networking,
keeping feature code declarative.

## Cross-cutting concerns

- **Config**: `backend/app/core/config.py` (Pydantic Settings) and
  `frontend/lib/config.ts`. One source of truth per service, environment-driven.
- **Logging**: centralised `app/core/logging.py`.
- **Database**: engine + session in `app/db`; schema changes only via Alembic
  migrations. `pool_pre_ping` guards against stale connections.
- **Errors**: a uniform envelope (`ApiResponse` / `ApiErrorResponse`) so client
  handling is consistent.
- **Containers**: non-root runtime users, pinned base images, healthchecks, and
  dependency order in docker-compose.

## Evolution path

The [roadmap](roadmap.md) tracks delivery phase by phase. High-level direction:

1. ~~Domain model for shipments, batches, sensors, routes~~ — done (Phase 2).
2. ~~Auth (JWT) wired through `app/core/security.py`~~ — done (Phase 3).
3. ~~Excursion-prediction engine behind an isolated, swappable port~~ — done
   (Phase 5.4): the rule engine (`score_excursion_risk`) is the scoring port;
   an XGBoost model can replace it behind the same interface.
4. Route recommendation engine (safe-route scoring + alternatives) — next
   (Phase 6).
5. Background telemetry ingestion (message queue) for nationwide scale.
6. ML model swap behind the prediction and route scoring ports.
