# DevOps & Deployment Guide

This document covers Docker setup, CI/CD, monitoring, and database migrations.

## 📦 Quick Start with Docker

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

### 2. Start the Stack

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access Services

| Service    | URL                        | Description           |
| ---------- | -------------------------- | --------------------- |
| Frontend   | http://localhost:3000      | React Dashboard       |
| Backend    | http://localhost:8000      | FastAPI API           |
| API Docs   | http://localhost:8000/docs | Swagger UI            |
| Prometheus | http://localhost:9090      | Metrics (optional)    |
| Grafana    | http://localhost:3001      | Dashboards (optional) |

---

## 🐳 Docker Configuration

### Services Overview

```yaml
services:
  database: # PostgreSQL 15
  backend: # Python FastAPI
  frontend: # React + Nginx
  prometheus: # Monitoring (optional)
  grafana: # Dashboards (optional)
```

### Build Images Individually

```bash
# Backend only
docker build -t anomaly-backend ./backend

# Frontend only
docker build -t anomaly-frontend ./frontend

# With custom API URL
docker build --build-arg REACT_APP_API_URL=https://api.example.com -t anomaly-frontend ./frontend
```

### Environment Variables

| Variable            | Default   | Description                  |
| ------------------- | --------- | ---------------------------- |
| `POSTGRES_USER`     | stockuser | Database username            |
| `POSTGRES_PASSWORD` | -         | Database password (required) |
| `POSTGRES_DB`       | stock_db  | Database name                |
| `BACKEND_PORT`      | 8000      | Backend API port             |
| `FRONTEND_PORT`     | 3000      | Frontend port                |
| `LOG_LEVEL`         | INFO      | Logging level                |
| `LOG_FORMAT`        | json      | `json` or `text`             |

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) includes:

1. **Backend Tests**
   - Python linting (flake8)
   - Unit tests (pytest)
   - Coverage reporting

2. **Frontend Tests**
   - ESLint
   - Jest tests
   - Build verification

3. **Docker Build**
   - Multi-stage builds
   - Image push to GHCR

4. **Security Scan**
   - Trivy vulnerability scanning

5. **Deployment** (manual trigger)

### Running Locally

```bash
# Run tests
make test

# Run linting
make lint

# Build Docker images
make docker-build
```

---

## 📊 Monitoring

### Enable Monitoring Stack

```bash
# Start with Prometheus + Grafana
docker-compose --profile monitoring up -d
```

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

| Metric                          | Type      | Description         |
| ------------------------------- | --------- | ------------------- |
| `http_requests_total`           | Counter   | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency     |
| `anomaly_detection_runs_total`  | Counter   | Detection runs      |
| `anomalies_detected_total`      | Counter   | Anomalies found     |
| `model_cache_hits_total`        | Counter   | Model cache hits    |
| `db_queries_total`              | Counter   | Database queries    |

### Grafana Dashboards

1. Access Grafana at http://localhost:3001
2. Login with admin/admin (change on first login)
3. Add Prometheus data source: http://prometheus:9090
4. Import dashboards from `monitoring/grafana/dashboards/`

---

## 🗃️ Database Migrations

### Using Alembic

```bash
# Run all pending migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new column"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Migration Workflow

1. Modify models in `data_storage/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review generated migration in `alembic/versions/`
4. Apply: `alembic upgrade head`

---

## 📝 Structured Logging

### Configuration

Set environment variables:

```bash
LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json   # json or text
```

### JSON Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "main",
  "message": "Request processed",
  "extra": {
    "request_id": "abc123",
    "duration_seconds": 0.125
  }
}
```

### Using in Code

```python
from logging_config import get_logger, LogContext, log_execution_time

logger = get_logger(__name__)

# Basic logging
logger.info("Processing request", extra={"user_id": 123})

# Context manager for request tracking
with LogContext(request_id="abc123", user_id="456"):
    logger.info("Processing")  # Includes context fields

# Decorator for timing
@log_execution_time()
def slow_function():
    ...
```

---

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Configure `REACT_APP_API_URL` for production domain
- [ ] Enable HTTPS (use reverse proxy like Traefik/Nginx)
- [ ] Set `LOG_FORMAT=json` for log aggregation
- [ ] Configure alerts (email/Slack/Discord)
- [ ] Set up database backups
- [ ] Review security headers

### Docker Compose Production Override

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"
services:
  backend:
    restart: always
    environment:
      LOG_LEVEL: WARNING
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G

  frontend:
    restart: always
```

Deploy with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Health Checks

| Service  | Endpoint          | Expected                |
| -------- | ----------------- | ----------------------- |
| Backend  | `GET /api/health` | `{"status": "healthy"}` |
| Backend  | `GET /api/ready`  | `{"ready": true}`       |
| Frontend | `GET /health`     | `healthy`               |

---

## 🛠️ Troubleshooting

### Common Issues

**Database connection failed:**

```bash
# Check database is running
docker-compose logs database

# Verify connection
docker-compose exec backend python -c "from data_storage.database import db; print(db.health_check())"
```

**Frontend can't reach backend:**

```bash
# Check CORS settings
# Verify REACT_APP_API_URL in frontend build
docker-compose exec frontend env | grep REACT
```

**Migrations failing:**

```bash
# Check current migration state
docker-compose exec backend alembic current

# Force to specific revision
docker-compose exec backend alembic stamp head
```

### Useful Commands

```bash
# View running containers
docker-compose ps

# Shell into container
docker-compose exec backend bash

# View real-time logs
docker-compose logs -f backend

# Restart single service
docker-compose restart backend

# Rebuild without cache
docker-compose build --no-cache backend
```

---

## 📁 File Structure

```
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions pipeline
├── backend/
│   ├── Dockerfile             # Backend Docker image
│   ├── alembic/               # Database migrations
│   ├── logging_config.py      # Structured logging
│   └── metrics.py             # Prometheus metrics
├── frontend/
│   ├── Dockerfile             # Frontend Docker image
│   └── nginx.conf             # Nginx configuration
├── database/
│   └── init.sql               # Database initialization
├── monitoring/
│   └── prometheus.yml         # Prometheus config
├── docker-compose.yml         # Container orchestration
├── Makefile                   # Development commands
└── .env.example               # Environment template
```
