#!/usr/bin/env bash
# Run backend quality gates: lint, type-check, and tests.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> ruff lint"
ruff check app tests

echo "==> ruff format check"
ruff format --check app tests

echo "==> mypy"
mypy app

echo "==> pytest"
pytest
