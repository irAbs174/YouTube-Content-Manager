# ── YouTube Content Manager — orchestration entrypoint ────────────────────────
# `make help` lists every target. Backend deps live in backend/.venv.

BACKEND_DIR := backend
VENV        := $(BACKEND_DIR)/.venv
PIP         := $(VENV)/bin/pip
PY          := $(VENV)/bin/python
RUFF        := $(VENV)/bin/ruff
UVICORN     := $(VENV)/bin/uvicorn

.DEFAULT_GOAL := help
.PHONY: help install backend frontend dev test test-backend test-frontend lint typecheck clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend (venv) + frontend (npm) dependencies
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt -r $(BACKEND_DIR)/requirements-dev.txt
	npm install

backend: ## Run the FastAPI backend with reload on :8000
	cd $(BACKEND_DIR) && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run the Next.js dev server on :3000 (proxies /api → :8000)
	npm run dev

dev: ## Run backend + frontend together (see scripts/dev.sh)
	./scripts/dev.sh

test: test-backend test-frontend ## Run every test suite

test-backend: ## pytest (FastAPI backend)
	cd $(BACKEND_DIR) && .venv/bin/python -m pytest

test-frontend: ## vitest (frontend logic)
	npm run test

lint: ## ruff + eslint
	cd $(BACKEND_DIR) && .venv/bin/ruff check app tests
	npm run lint

typecheck: ## TypeScript strict check
	npm run typecheck

clean: ## Remove build artifacts and local runtime data
	rm -rf .next backend/data backend/.pytest_cache
