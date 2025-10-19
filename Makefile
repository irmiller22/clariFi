.PHONY: help install test test-backend test-frontend lint format run-backend run-frontend build-frontend clean

# Default target
help:
	@echo "Range Finance - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-backend  Install backend dependencies"
	@echo "  make install-frontend Install frontend dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests (backend + frontend)"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-frontend    Run frontend tests"
	@echo "  make test-coverage    Run backend tests with coverage"
	@echo ""
	@echo "Development:"
	@echo "  make run-backend      Start FastAPI backend server"
	@echo "  make run-frontend     Start Next.js dev server"
	@echo "  make build-frontend   Build frontend for production"
	@echo "  make lint             Run linters on all code"
	@echo "  make lint-frontend    Run frontend linter"
	@echo "  make format           Format all code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"

# Installation
install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies with uv..."
	cd backend && uv sync

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend && uv run python -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	@echo "Frontend tests not yet implemented"

test-coverage:
	@echo "Running backend tests with coverage..."
	cd backend && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# Development
run-backend:
	@echo "Starting FastAPI backend server..."
	cd backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting Next.js dev server..."
	cd frontend && npm run dev

build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

# Code Quality
lint: lint-frontend

lint-frontend:
	@echo "Running frontend linter..."
	cd frontend && npm run lint

format:
	@echo "Formatting code..."
	@echo "Formatting not yet configured"

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf frontend/.next 2>/dev/null || true
	rm -rf frontend/out 2>/dev/null || true
	@echo "Clean complete!"
