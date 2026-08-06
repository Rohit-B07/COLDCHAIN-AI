"""Pytest suite.

Test files are grouped by layer to mirror the application structure:

- tests/unit      -> pure domain + use-case logic (no DB, no network)
- tests/integration -> repositories against a real (test) database
- tests/api       -> FastAPI test client exercising endpoints

Fixtures shared across the suite live in tests/conftest.py.
"""
