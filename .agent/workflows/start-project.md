---
description: How to start the Stock Anomaly Detection project (backend, frontend, and database)
---

# 🚀 Starting the Stock Anomaly Detection Project

This workflow provides step-by-step instructions to start the project locally. Choose either **Docker (Recommended)** or **Manual Setup** based on your preference.

---

## Prerequisites

Before starting, ensure you have the following installed:

### For Docker Setup (Recommended)

- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Docker Compose** (included with Docker Desktop)

### For Manual Setup

- **Python 3.11+**
- **Node.js 18+** (20 recommended)
- **PostgreSQL 15+** (running locally or accessible)
- **pip** (Python package manager)
- **npm 8+** (Node package manager)

---

## Option 1: Docker Setup (Recommended)

This is the simplest way to start all services with a single command.

### Step 1: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit the `.env` file with your preferred settings:

```env
# Database credentials
POSTGRES_USER=stockuser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=stock_db
DB_PORT=5432

# Backend configuration
BACKEND_PORT=8000
LOG_LEVEL=INFO
LOG_FORMAT=json

# Frontend configuration
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000

# Monitoring (optional)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Alerts (optional)
ALERT_EMAIL_ENABLED=false
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
```

### Step 2: Start All Services

```bash
# Build and start all containers
docker-compose up -d
```

This starts:

- **PostgreSQL Database** on port 5432
- **Backend API** on port 8000
- **Frontend** on port 3000

### Step 3: Verify Services Are Running

```bash
# Check container status
docker-compose ps

# View logs (optional)
docker-compose logs -f
```

### Step 4: Access the Application

| Service      | URL                              | Description           |
| ------------ | -------------------------------- | --------------------- |
| Frontend     | http://localhost:3000            | Main application UI   |
| Backend API  | http://localhost:8000            | REST API server       |
| API Docs     | http://localhost:8000/docs       | Swagger documentation |
| Health Check | http://localhost:8000/api/health | API health status     |

### Step 5 (Optional): Start with Monitoring

To include Prometheus and Grafana monitoring:

```bash
docker-compose --profile monitoring up -d
```

Access monitoring:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### Stopping Docker Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

---

## Option 2: Manual Setup

Use this method for local development or if Docker is not available.

### Step 1: Setup PostgreSQL Database

#### Option A: Using Local PostgreSQL Installation

1. **Install PostgreSQL 15+** if not already installed
2. **Create the database and user**:

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create the database user
CREATE USER stockuser WITH PASSWORD 'your_secure_password';

-- Create the database
CREATE DATABASE stock_db OWNER stockuser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE stock_db TO stockuser;

-- Exit
\q
```

#### Option B: Using Docker for Database Only

```bash
docker run -d \
  --name anomaly-db \
  -e POSTGRES_USER=stockuser \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=stock_db \
  -p 5432:5432 \
  postgres:15-alpine
```

### Step 2: Setup Backend

#### 2.1 Navigate to Backend Directory

```bash
cd backend
```

#### 2.2 Create Python Virtual Environment

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate
```

#### 2.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 2.4 Configure Backend Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your database credentials
```

Update `backend/.env`:

```env
# Required: Database connection string
DATABASE_URL=postgresql://stockuser:your_secure_password@localhost:5432/stock_db

# Optional: Logging
LOG_LEVEL=INFO
LOG_FORMAT=text

# Optional: API settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Optional: Alerts (configure if needed)
ALERT_EMAIL_ENABLED=false
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
```

#### 2.5 Run Database Migrations

```bash
alembic upgrade head
```

This creates all required database tables.

#### 2.6 (Optional) Add Sample Data

```bash
python add_sample_data.py
```

#### 2.7 Start Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at http://localhost:8000

### Step 3: Setup Frontend

#### 3.1 Open New Terminal & Navigate to Frontend

```bash
cd frontend
```

#### 3.2 Install Node Dependencies

```bash
npm install
```

#### 3.3 Configure Frontend Environment (Optional)

```bash
# Create local environment file
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
```

#### 3.4 Start Frontend Development Server

```bash
npm start
```

The frontend is now available at http://localhost:3000

---

## Quick Reference: Makefile Commands

If you have `make` installed, you can use these shortcuts:

```bash
# Install all dependencies
make install

# Start development servers (requires Unix-like shell)
make dev

# Run tests
make test

# Run database migrations
make migrate

# Docker commands
make docker-up      # Start Docker containers
make docker-down    # Stop Docker containers
make docker-logs    # View logs
make docker-build   # Build images
```

---

## Verification Checklist

After starting the project, verify everything is working:

1. **Database Connection**
   - Backend logs show "Database connected" or similar
   - No connection errors in backend output

2. **Backend API**
   - Visit http://localhost:8000/api/health → Should return `{"status": "healthy"}`
   - Visit http://localhost:8000/docs → Should show Swagger UI

3. **Frontend**
   - Visit http://localhost:3000 → Should load the dashboard
   - No CORS errors in browser console
   - API health indicator shows "connected"

4. **End-to-End**
   - Select a stock symbol in the dropdown
   - Click "Detect Anomalies" → Should process and show results

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps database  # Docker
pg_isready -h localhost     # Local PostgreSQL

# Verify connection string in backend/.env
# Ensure password contains no special chars that need escaping
```

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS

# Change ports in .env or docker-compose.yml
```

### Frontend Can't Connect to Backend

1. Ensure backend is running on http://localhost:8000
2. Check `REACT_APP_API_URL` in frontend/.env.local
3. Verify CORS is configured in backend

### Docker Issues

```bash
# Rebuild containers from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# View detailed logs
docker-compose logs backend
docker-compose logs database
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                    http://localhost:3000                     │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│               (Dashboard, Charts, Controls)                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│          http://localhost:8000/api/*                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Data        │  │ Anomaly    │  │ Alert System        │   │
│  │ Collection  │  │ Detection  │  │ (Email/Slack/Discord)│  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└────────────────────────────┬─────────────────────────────────┘
                             │ SQL
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│                    localhost:5432                            │
│        (stocks, stock_data, anomalies tables)                │
└──────────────────────────────────────────────────────────────┘
```

---

## Next Steps After Starting

1. **Add Stock Symbols**: Use the API or UI to add stocks to monitor
2. **Collect Data**: Backend fetches historical data from Yahoo Finance
3. **Detect Anomalies**: Run detection algorithms on collected data
4. **Configure Alerts**: Set up email/Slack/Discord notifications
5. **Monitor**: Use Prometheus/Grafana for system metrics

---

## 🧪 Testing (Optional)

Run the test suite to verify everything is working:

```bash
# Navigate to backend
cd backend

# Run all tests
pytest -v

# Run with coverage report
pytest -v --cov=anomaly_detection --cov-report=html

# Skip slow ML model tests
pytest -m "not slow" -v

# View coverage report (Windows)
start htmlcov/index.html
```

---

## 🔄 Model Retraining (Optional)

Retrain ML models with fresh data:

```bash
cd backend

# Retrain all models for all symbols
python scripts/scheduled_retrain.py --all

# Retrain specific model
python scripts/scheduled_retrain.py --symbol AAPL --model isolation_forest

# Cleanup expired models (older than 24 hours)
python scripts/scheduled_retrain.py --cleanup --max-age 24
```

---

## 📓 Jupyter Notebooks

The project includes notebooks for model evaluation:

| Notebook         | Description                            | Location                                      |
| ---------------- | -------------------------------------- | --------------------------------------------- |
| GPU Training     | Train advanced models on Google Colab  | `notebooks/GPU_Training_Colab.ipynb`          |
| Model Benchmarks | Evaluate and compare model performance | `notebooks/Model_Evaluation_Benchmarks.ipynb` |

---

## 📚 Additional Documentation

| Document                                                             | Description                        |
| -------------------------------------------------------------------- | ---------------------------------- |
| [README.md](../README.md)                                            | Project overview and features      |
| [DEVOPS.md](../DEVOPS.md)                                            | Docker, CI/CD, monitoring guide    |
| [MODEL_RETRAINING_PIPELINE.md](../docs/MODEL_RETRAINING_PIPELINE.md) | MLOps and retraining documentation |
| [Backend README](../backend/README.md)                               | API endpoints and backend setup    |
