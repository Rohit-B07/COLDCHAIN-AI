# ColdChain AI

**AI-powered decision support for vaccine cold-chain delivery.**

Predicts vaccine **temperature excursions before dispatch** and recommends the
**safest delivery route** — built as a Smart India Hackathon prototype with
production-grade engineering practices so it can scale into a nationwide
healthcare platform.

## Stack

| Layer      | Technology                                   |
| ---------- | -------------------------------------------- |
| Frontend   | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend    | FastAPI, Python 3.11, Pydantic v2            |
| Database   | PostgreSQL 16, SQLAlchemy 2, Alembic         |
| Infra      | Docker, Docker Compose                       |
| Quality    | Ruff, mypy, pytest, ESLint, Prettier, pre-commit |

## Repository layout

```
.
├── backend/              # FastAPI service (Clean Architecture)
│   ├── app/
│   │   ├── api/          # HTTP layer: routers, DI wiring
│   │   ├── core/         # config, logging, security
│   │   ├── db/           # SQLAlchemy engine, session, Base
│   │   ├── domain/       # pure entities, value objects, ports
│   │   ├── models/       # ORM models (persistence mapping)
│   │   ├── repositories/ # port implementations (SQLAlchemy)
│   │   ├── schemas/      # Pydantic request/response DTOs
│   │   ├── services/     # cross-cutting business services
│   │   └── use_cases/    # application layer business actions
│   ├── migrations/       # Alembic migrations
│   ├── tests/            # unit / integration / API tests
│   └── scripts/          # dev & quality helpers
├── frontend/             # Next.js application
│   ├── app/              # App Router pages & layouts
│   ├── components/       # ui/ (shadcn) + layout + shared
│   ├── features/         # feature-scoped modules (D2C)
│   ├── hooks/            # shared client hooks
│   └── lib/              # config, API client, types, utils
├── docs/                 # architecture, standards, conventions
├── infra/                # infrastructure extras (future)
├── docker-compose.yml    # db + backend + frontend
├── Makefile              # command aliases
└── .env.example          # environment template
```

## Quick start

### 1. Environment

Copy the template and adjust values (development defaults work out of the box):

```bash
cp .env.example .env
cp backend/.env.example backend/.env        # optional
cp frontend/.env.example frontend/.env.local
```

### 2. Run the full stack (Docker)

```bash
docker compose up --build -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs

### 3. Run locally (without Docker)

Requires a reachable PostgreSQL instance.

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
./scripts/dev.sh

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

## Make targets

| Target | Description                     |
| ------ | ------------------------------- |
| `make up` | Build & start full stack     |
| `make down` | Stop containers            |
| `make logs` | Tail service logs          |
| `make dev-backend` | Run backend locally    |
| `make dev-frontend` | Run frontend locally  |
| `make test-backend` | Lint + type-check + tests |
| `make fmt` | Format frontend            |

## Quality gates

```bash
cd backend && ./scripts/quality.sh   # ruff, mypy, pytest
cd frontend && npm run quality       # eslint, tsc
```

pre-commit is configured; install it once with `pre-commit install`.

## Documentation

- [Architecture](docs/architecture.md) — design decisions, layering, trade-offs
- [Coding standards](docs/coding-standards.md) — language-specific rules
- [Conventions](docs/conventions.md) — project workflow and conventions

## Status

Phases 1–5.4 are complete: the foundation, core domain, authentication & RBAC,
facility/logistics/shipment management, weather service, alerting, the
operations dashboard, and the **temperature excursion prediction engine**
(rule-based, explainable, RBAC-protected) are all shipped with tests.

**Next: Phase 6 — Route Recommendation Engine** (safest-route scoring with
alternatives, persistence and a routes UI). See [Roadmap](docs/roadmap.md).
