# Project conventions

## Feature workflow

1. **Domain first.** Define the business concept as pure entities and value
   objects in `backend/app/domain`, with the port (protocol) it needs.
2. **Application.** Implement the use case in `app/use_cases` against the port.
3. **Infrastructure.** Add the ORM model in `app/models`, the repository
   implementation in `app/repositories`, and a schema migration in
   `migrations/`.
4. **API.** Expose the route in `app/api/routes` and wire dependencies in
   `app/api/deps/container.py`.
5. **Frontend.** Mirror the capability as a `frontend/features/<name>` module
   with typed DTOs in `frontend/lib/types`.
6. **Test.** Unit tests for domain/use cases, API tests with dependency
   overrides, and client-side type/lint checks.

## Environment management

- Real secrets never enter the repository. All templates end in `.env.example`.
- `backend/.env` is loaded by Pydantic Settings at runtime.
- `frontend/.env.local` is loaded by Next.js at build/dev time; only
  `NEXT_PUBLIC_*` variables are exposed to the browser.
- docker-compose reads the root `.env` for shared values and passes them to
  services explicitly.

## Database changes

- **Never** create/alter tables by hand. Generate migrations:

  ```bash
  cd backend
  alembic revision --autogenerate -m "describe change"
  alembic upgrade head
  ```

- Model additions must be imported in `app/db/base.py` so Alembic sees them.
- Review generated migrations before committing.

## Naming & structure

### Backend

| Concern          | Location              | Example                    |
| ---------------- | --------------------- | -------------------------- |
| HTTP routes      | `app/api/routes/`     | `shipments.py`             |
| DI wiring        | `app/api/deps/`       | `container.py`             |
| Use cases        | `app/use_cases/`      | `predict_excursion.py`     |
| Domain entities  | `app/domain/entities/`| `shipment.py`              |
| Value objects    | `app/domain/value_objects/` | `temperature.py`     |
| Ports            | `app/domain/repositories/`  | `shipment.py`        |
| Repos (impl)     | `app/repositories/`   | `shipment.py`              |
| ORM models       | `app/models/`         | `shipment.py`              |
| Schemas          | `app/schemas/`        | `shipment.py`              |

One file per aggregate/concept. Use singular nouns for entity/model filenames.

### Frontend

| Concern        | Location                 |
| -------------- | ------------------------ |
| Feature module | `features/<feature>/`    |
| UI primitives  | `components/ui/`         |
| Layout         | `components/layout/`     |
| Shared hooks   | `hooks/`                 |
| Config         | `lib/config.ts`          |
| API client     | `lib/api/client.ts`      |
| Types          | `lib/types/`             |
| Utilities      | `lib/utils.ts`           |

A feature folder exports its public surface from `index.ts`; everything else
stays private to the folder.

## API conventions

- Endpoints live under `/api/v1`.
- All responses use the uniform envelope in `app/schemas/common.py`.
- Feature routers are registered in `app/api/routes/__init__.py`.
- New endpoints include OpenAPI summary/description and are grouped by tags.

## Quality gates before you finish

Run the full set and leave the tree clean:

```bash
cd backend && ./scripts/quality.sh
cd frontend && npm run quality
```

pre-commit runs `ruff` (backend) and `prettier` (frontend) automatically.

## Review checklist

- [ ] No secrets or absolute local paths committed
- [ ] Domain layer imports nothing framework-specific
- [ ] New models have a corresponding Alembic migration
- [ ] Types/DTOs added for any new API surface
- [ ] Unit/API tests cover the new behaviour
- [ ] `quality` gates pass for both services
- [ ] Docs updated if behaviour or layout changed
