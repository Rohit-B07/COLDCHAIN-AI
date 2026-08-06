# Coding standards

These rules apply to all code written in this repository. They are enforced
where possible by the tooling configured in each service (`pyproject.toml`,
`eslint.config.mjs`, `.prettierrc.json`).

## General principles

- Follow **Clean Architecture**, **SOLID**, **DRY**, and **KISS**.
- No placeholder implementations. If a feature is not ready, it is omitted,
  not stubbed with `pass`/`TODO` (unless a clear, meaningful `TODO` is recorded,
  which is acceptable and encouraged to track follow-up work).
- Keep functions and components small and single-purpose.
- No dead code, commented-out code, or unused imports.
- Prefer explicit over implicit; name things for intent.

## Python (backend)

- **Formatting / linting**: `ruff` with the ruleset in `backend/pyproject.toml`
  (line length 88, double quotes). Run `ruff format` and `ruff check`.
- **Typing**: strict mypy profile (`disallow_untyped_defs = true`). Annotate
  every public function signature and module/class docstring.
- **Layer discipline**:
  - `app/domain`: pure Python (no FastAPI/SQLAlchemy/Pydantic). Use
    `dataclasses` and `Protocol` for ports.
  - `app/use_cases` / `app/services`: depend only on domain interfaces.
  - `app/api`: only DTOs (Pydantic), routers, and DI wiring.
- **Imports**: absolute imports, standard-library → third-party → app (isort
  via ruff `I`).
- **Exceptions**: raise domain-meaningful `ValueError`/custom exceptions;
  validate at the boundary (schemas) and in value objects.
- **Tests** (`pytest`): pure-logic tests in `tests/unit`, HTTP tests in
  `tests/api` with dependency overrides, integration tests in `tests/integration`.

### Ruff quick reference

```bash
cd backend
ruff check .                 # lint
ruff format .                # format
mypy app                     # type-check
pytest                       # run tests
```

## TypeScript / React (frontend)

- **Strict TypeScript** (`tsconfig.json` sets `strict`, `noUncheckedIndexedAccess`).
- **Components**:
  - Client components that need state/interactivity are marked `"use client"`.
  - Server components by default; keep them lean and free of client hooks.
  - shadcn/ui primitives live in `components/ui` and are generated via CLI.
- **Formatting**: Prettier with `prettier-plugin-tailwindcss` (see `.prettierrc.json`).
- **Linting**: ESLint flat config (`eslint.config.mjs`, `next/core-web-vitals`).
- **Naming**:
  - Components: `PascalCase.tsx`, one component per file (default export).
  - Hooks: `useCamelCase` under `hooks/` or `features/<feature>/`.
  - Utilities/constants: `camelCase`.
- **Path alias**: `@/*` maps to the frontend root. Use it instead of relative
  imports.
- **Styling**: Tailwind utilities only; CSS variables via shadcn theme tokens.
  No inline `style` for layout.
- **Accessibility**: semantic markup, `aria-*` attributes, focus-visible rings.
- **Data fetching**: only through `lib/api/client.ts`; never call `fetch`
  directly in components.

### Frontend checks

```bash
cd frontend
npm run lint          # eslint
npm run typecheck     # tsc --noEmit
npm run format        # prettier --write
```

## Documentation & comments

- Use docstrings on Python modules, classes, and public functions.
- Prefer descriptive code over comments. Add a comment only to explain **why**.
- Keep `README`, `docs/*`, and `AGENTS.md`-style guidance in sync with reality.

## Commit conventions

- Write a concise imperative subject line (e.g. "Add health check endpoint").
- Group logically related changes; never commit secrets or generated artifacts.
- Follow Conventional Commits prefixes for clarity:
  `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`.