.PHONY: help setup up down dev api front front-setup dev-all test test-all lint fmt migrate migration detect upload clean

BACKEND := backend
UV := uv --project $(BACKEND)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and create .env if missing
	$(UV) sync
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

up: ## Start postgres + minio
	docker compose up -d
	@echo "Waiting for postgres..."
	@until docker compose exec -T postgres pg_isready -U rpf >/dev/null 2>&1; do sleep 1; done
	@echo "Ready."

down: ## Stop the containers
	docker compose down

dev: setup up migrate api ## Full local startup: deps, containers, migrations, API

api: ## Run the API with reload
	$(UV) run uvicorn rpf.main:app --reload --host 0.0.0.0 --port 8000

front-setup: ## Install frontend dependencies and create frontend/.env if missing
	cd frontend && npm install
	@test -f frontend/.env || (cp frontend/.env.example frontend/.env && echo "Created frontend/.env from frontend/.env.example")

front: ## Run the frontend dev server
	cd frontend && npm run dev

dev-all: setup up migrate front-setup ## Backend + frontend together in one terminal (Ctrl+C stops both)
	@trap 'kill 0' EXIT INT TERM; \
	($(UV) run uvicorn rpf.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev)

# These cd into backend/ so pytest and ruff pick up backend/pyproject.toml.
# Run from the repo root and its [tool.pytest.ini_options] is silently ignored,
# which loses the marker registry and pythonpath.
test: ## Run tests (unit only; M="integration" for the rest)
	cd $(BACKEND) && uv run pytest -m "$(or $(M),not integration)" -q

test-all: ## Run every test, including integration (needs make up)
	cd $(BACKEND) && uv run pytest -q

lint: ## Lint and check formatting
	cd $(BACKEND) && uv run ruff check src tests
	cd $(BACKEND) && uv run ruff format --check src tests

fmt: ## Auto-format and fix lint issues
	cd $(BACKEND) && uv run ruff format src tests
	cd $(BACKEND) && uv run ruff check --fix src tests

migrate: ## Apply all migrations
	cd $(BACKEND) && uv run alembic upgrade head

migration: ## Create a migration: make migration M="add orders table"
	@test -n "$(M)" || (echo 'Usage: make migration M="description"' && exit 1)
	cd $(BACKEND) && uv run alembic revision --autogenerate -m "$(M)"

detect: ## Detect bibs: make detect F=samples/photos E=my-race
	@test -n "$(F)" -a -n "$(E)" || (echo 'Usage: make detect F=<folder> E=<event-slug>' && exit 1)
	$(UV) run rpf detect $(F) --event $(E)

upload: ## Upload photos: make upload F=samples/photos E=my-race
	@test -n "$(F)" -a -n "$(E)" || (echo 'Usage: make upload F=<folder> E=<event-slug>' && exit 1)
	$(UV) run rpf upload --event $(E) --manifest $(F)/manifest.json --create-event

clean: ## Remove local storage and caches
	rm -rf $(BACKEND)/var/storage
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
