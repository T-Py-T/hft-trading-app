# hft-trading-app/Makefile
# HFT Trading Platform - Docker compose and integration test orchestration
# Does NOT: Build individual components, deploy to production, manage git

.PHONY: help up down logs test test-all clean build-images ps health setup

help:
	@echo "HFT Trading Platform - Integration Orchestration"
	@echo ""
	@echo "Container Management:"
	@echo "  make up             - Start all services (PostgreSQL, C++ engine, Go backend)"
	@echo "  make down           - Stop all services"
	@echo "  make ps             - Show service status"
	@echo "  make logs           - View logs from all services"
	@echo "  make health         - Check service health"
	@echo ""
	@echo "Setup & Maintenance:"
	@echo "  make clean          - Stop services and cleanup volumes"
	@echo "  make build-images   - Build container images from source"
	@echo ""
	@echo "tests/integration_test.py targets the historical Python FastAPI surface"
	@echo "and is excluded from pytest discovery; manifest checks remain active."
	@echo "The Go backend's own end-to-end suite runs in ml-trading-app-go CI."
	@echo ""

up:
	@echo "Starting HFT Trading Platform..."
	@docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@make health

down:
	@echo "Stopping HFT Trading Platform..."
	@docker-compose down

ps:
	@docker-compose ps

logs:
	@docker-compose logs -f

health:
	@echo "Checking service health..."
	@docker-compose ps --format "table {{.Service}}\t{{.Status}}"

# These Compose-backed targets remain opt-in; pytest itself discovers the active
# manifest checks and excludes legacy tests/integration_test.py by default.
SKIP_TESTS ?= 1

setup:
	@echo "Setting up test database..."
	@bash scripts/setup_test_db.sh
	@echo "Test database ready!"

test: up setup
	@if [ "$(SKIP_TESTS)" = "1" ]; then \
	  echo "Compose-backed test target skipped. Run with SKIP_TESTS=0; pytest excludes legacy integration_test.py."; \
	else \
	  echo "Running integration tests..."; \
	  python -m pytest tests/ -v; \
	fi

test-all: up setup
	@if [ "$(SKIP_TESTS)" = "1" ]; then \
	  echo "Compose-backed test target skipped. Run with SKIP_TESTS=0; pytest excludes legacy integration_test.py."; \
	else \
	  echo "Running all integration tests with coverage..."; \
	  python -m pytest tests/ -v --cov=tests --cov-report=html; \
	  echo "Coverage report generated in htmlcov/"; \
	fi

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@rm -rf htmlcov .pytest_cache __pycache__ .coverage
	@echo "Cleanup complete"

build-images:
	@echo "Building container images from source..."
	@docker-compose build --no-cache

.DEFAULT_GOAL := help
