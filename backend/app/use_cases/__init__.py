"""Application layer: use cases and services.

Use cases orchestrate the flow of data between the controllers (API) and the
domain, implementing a single business action each. Services hold cross-cutting
or shared business logic reused by multiple use cases. Both depend on domain
interfaces only — never on FastAPI or SQLAlchemy.
"""
