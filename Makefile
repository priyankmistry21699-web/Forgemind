# ============================================================
# ForgeMind — Developer Commands
# ============================================================

.PHONY: help dev dev-api dev-web dev-worker docker-up docker-down \
        test test-api test-web lint format migrate migrate-create \
        install install-api install-web clean

# ---- Help ----
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Development ----
dev: ## Run all services in development mode
	docker compose up -d postgres redis
	@echo "Starting API and Web in parallel..."
	$(MAKE) dev-api &
	$(MAKE) dev-web &
	wait

dev-api: ## Run FastAPI dev server
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Run Next.js dev server
	cd apps/web && npm run dev

dev-worker: ## Run Celery worker
	cd apps/worker && celery -A worker.main worker --loglevel=info

# ---- Docker ----
docker-up: ## Start infrastructure (Postgres, Redis, MinIO)
	docker compose up -d

docker-down: ## Stop infrastructure
	docker compose down

docker-build: ## Build all containers
	docker compose build

# ---- Install ----
install: install-api install-web ## Install all dependencies

install-api: ## Install Python backend dependencies
	cd apps/api && pip install -e ".[dev]"

install-web: ## Install Node.js frontend dependencies
	cd apps/web && npm install

# ---- Database ----
migrate: ## Run database migrations
	cd apps/api && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

# ---- Testing ----
test: test-api test-web ## Run all tests

test-api: ## Run backend tests
	cd apps/api && pytest -v

test-web: ## Run frontend tests
	cd apps/web && npm test

# ---- Code Quality ----
lint: ## Run linters
	cd apps/api && ruff check .
	cd apps/web && npm run lint

format: ## Format code
	cd apps/api && ruff format .
	cd apps/web && npm run format

# ---- Cleanup ----
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name .next -exec rm -rf {} +
