.PHONY: setup run test test-cov lint lint-fix format check clean help

setup: ## Install development dependencies
	@echo "Installing dependencies..."
	uv sync --all-extras

run: ## Start the application
	@echo "Starting application..."
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

test: ## Run pytest test suite
	@echo "Running tests..."
	uv run pytest -v

test-cov: ## Run tests with coverage report
	@clear || cls
	@echo "Running tests with coverage..."
	uv run coverage run -m pytest
	uv run coverage xml
	uv run coverage report --show-missing

lint: ## Run Ruff linter
	@echo "Running linter..."
	uv run ruff check src

lint-fix: ## Auto-fix linting issues
	@echo "Fixing lint issues..."
	uv run ruff check --fix src

format: ## Format code with Ruff
	@echo "Formatting code..."
	uv run ruff format src

check: ## Run lint and format checks together
	@echo "Running checks..."
	uv run ruff check src
	uv run ruff format --check src

clean: ## Remove cache files
	@echo "Cleaning cache files..."
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

help: ## List all available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
