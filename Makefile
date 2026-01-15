# Makefile for HA AI Gen Workflow Development
# Provides convenient shortcuts for common development tasks

.PHONY: help install test lint format clean docker-test validate quick-validate coverage docs

# Default target
help:
	@echo "HA AI Gen Workflow - Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install         - Install development dependencies"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint            - Run linting checks"
	@echo "  make format          - Auto-format code"
	@echo "  make coverage        - Generate coverage report"
	@echo "  make validate        - Run full validation suite"
	@echo "  make quick-validate  - Run quick validation"
	@echo "  make docker-test     - Run tests in Docker"
	@echo "  make security        - Run security scans"
	@echo "  make clean           - Clean temporary files"
	@echo "  make docs            - Build documentation"
	@echo "  make pre-commit      - Setup pre-commit hooks"
	@echo ""

# Installation
install:
	@echo "Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements-test.txt
	@echo "✓ Installation complete"

# Testing
test:
	@echo "Running all tests..."
	pytest -v --cov=bin --cov-report=term --cov-report=html

test-unit:
	@echo "Running unit tests..."
	pytest -v -m unit

test-integration:
	@echo "Running integration tests..."
	pytest -v -m integration

test-watch:
	@echo "Running tests in watch mode..."
	ptw -- -v

# Linting and Formatting
lint:
	@echo "Running linting checks..."
	@echo "→ Black..."
	black --check --line-length 120 bin/
	@echo "→ Flake8..."
	flake8 bin/ --max-line-length=120 --ignore=E203,W503
	@echo "→ Pylint..."
	pylint bin/*.py || true
	@echo "→ ShellCheck..."
	shellcheck *.sh || true
	@echo "✓ Linting complete"

format:
	@echo "Auto-formatting code..."
	black --line-length 120 bin/
	@echo "✓ Formatting complete"

# Security
security:
	@echo "Running security scans..."
	@echo "→ Bandit..."
	bandit -r bin/ -ll -i
	@echo "→ Detecting secrets..."
	detect-secrets scan || true
	@echo "✓ Security scan complete"

# Coverage
coverage:
	@echo "Generating coverage report..."
	pytest --cov=bin --cov-report=html --cov-report=term
	@echo "✓ Coverage report: htmlcov/index.html"

# Validation
validate:
	@echo "Running full validation suite..."
	chmod +x tools/validate_all.sh
	./tools/validate_all.sh

quick-validate:
	@echo "Running quick validation..."
	chmod +x tools/quick_validate.sh
	./tools/quick_validate.sh

# Docker
docker-build:
	@echo "Building Docker test image..."
	docker build -f Dockerfile.test -t ha-ai-workflow-test .

docker-test:
	@echo "Running tests in Docker..."
	chmod +x tools/run_docker_tests.sh
	./tools/run_docker_tests.sh

docker-shell:
	@echo "Starting Docker development shell..."
	docker-compose -f docker-compose.test.yml run --rm dev

# Pre-commit
pre-commit:
	@echo "Setting up pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✓ Pre-commit hooks installed"

pre-commit-run:
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Documentation
docs:
	@echo "Building documentation..."
	@echo "Documentation is in Markdown format:"
	@echo "  - docs/complete_readme.md"
	@echo "  - docs/deployment_guide.md"
	@echo "  - docs/quick_reference.md"
	@echo "  - docs/fix_summary_guide.md"
	@echo "✓ Documentation ready"

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	rm -f validation.log 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Development workflow
dev-setup: install pre-commit
	@echo "Development environment ready!"
	@echo "Run 'make test' to verify everything works."

# CI/CD simulation
ci: lint test security
	@echo "✓ CI checks complete"
