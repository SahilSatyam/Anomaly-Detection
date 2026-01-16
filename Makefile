# Makefile for Stock Anomaly Detection
# Usage: make <target>

.PHONY: help install dev build test lint clean docker-build docker-up docker-down docker-logs migrate

# Default target
help:
	@echo "Stock Anomaly Detection - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development servers"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start all containers"
	@echo "  make docker-down  - Stop all containers"
	@echo "  make docker-logs  - View container logs"
	@echo "  make docker-shell - Open shell in backend container"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-new  - Create new migration"
	@echo "  make db-reset     - Reset database (DANGER!)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring   - Start with monitoring stack"

# ==================== Development ====================

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done!"

dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@trap 'kill 0' SIGINT; \
	cd backend && uvicorn main:app --reload --port 8000 & \
	cd frontend && npm start & \
	wait

test:
	@echo "Running backend tests..."
	cd backend && pytest -v --cov=. --cov-report=html
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage --watchAll=false

test-backend:
	cd backend && pytest -v --cov=. --cov-report=html

test-frontend:
	cd frontend && npm test -- --coverage --watchAll=false

lint:
	@echo "Linting backend..."
	cd backend && flake8 . --count --max-line-length=127 --statistics
	@echo "Linting frontend..."
	cd frontend && npm run lint --if-present

format:
	cd backend && black . --line-length 100

clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/build frontend/coverage
	rm -rf backend/__pycache__ backend/.pytest_cache backend/htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done!"

# ==================== Docker ====================

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec backend /bin/bash

docker-clean:
	docker-compose down -v --rmi local
	docker system prune -f

# ==================== Database ====================

migrate:
	cd backend && alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

migrate-down:
	cd backend && alembic downgrade -1

migrate-history:
	cd backend && alembic history

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cd backend && alembic downgrade base && alembic upgrade head; \
	fi

# ==================== Monitoring ====================

monitoring:
	docker-compose --profile monitoring up -d

monitoring-down:
	docker-compose --profile monitoring down

# ==================== Production ====================

build-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

deploy-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
