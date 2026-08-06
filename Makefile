# ColdChain AI - development command aliases.
# Requires GNU Make. On Windows use WSL or `npx`, `docker compose` directly.

.PHONY: help dev-backend dev-frontend build up down logs lint test test-backend fmt

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start the full stack (db + backend + frontend) with docker compose
	docker compose up --build -d

down: ## Stop and remove containers (volumes preserved)
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

build: ## Build images without starting
	docker compose build

dev-backend: ## Run the backend locally (needs a reachable Postgres)
	cd backend && ./scripts/dev.sh

dev-frontend: ## Run the frontend dev server locally
	cd frontend && npm run dev

test: test-backend ## Run all test suites
	cd frontend && npm run quality

test-backend: ## Run backend lint, type-check, and tests
	cd backend && ./scripts/quality.sh

fmt: ## Format frontend code with prettier
	cd frontend && npm run format