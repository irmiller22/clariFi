.PHONY: help install test test-backend test-frontend lint format run-backend run-frontend clean

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
	@echo "  make test-coverage    Run backend tests with coverage"
	@echo ""
	@echo "Development:"
	@echo "  make run-backend      Start FastAPI backend server"
	@echo "  make lint             Run linters on all code"
	@echo "  make format           Format all code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and caches"

# Installation
install: install-backend

install-backend:
	@echo "Installing backend dependencies with uv..."
	cd backend && uv sync

install-frontend:
	@echo "Installing frontend dependencies..."
	@echo "Frontend not yet implemented"

# Testing
test: test-backend

test-backend:
	@echo "Running backend tests..."
	cd backend && uv run python -m pytest tests/ -v

test-coverage:
	@echo "Running backend tests with coverage..."
	cd backend && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# Development
run-backend:
	@echo "Starting FastAPI backend server..."
	cd backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting frontend dev server..."
	@echo "Frontend not yet implemented"

# Code Quality
lint:
	@echo "Running linters..."
	@echo "Linting not yet configured"

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
	@echo "Clean complete!"
