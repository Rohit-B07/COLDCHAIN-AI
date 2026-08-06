"""Domain layer.

The domain layer contains the business heart of the system and must remain
free of any framework or infrastructure dependencies (SQLAlchemy, FastAPI,
Pydantic). It defines:

- `entities`: pure domain models describing the core business concepts.
- `repositories`: abstract interfaces (ports) that the application layer
  depends on and that the infrastructure layer implements.

Dependency rule: nothing in this package may import from `app.models`,
`app.db`, or `app.api`.
"""
