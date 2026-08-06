"""Shared pytest fixtures.

Environment is pinned to `testing` before any application import so that
tests never touch a development or production database.
"""

import os

os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://coldchain:coldchain@localhost:5432/coldchain_test"
)
