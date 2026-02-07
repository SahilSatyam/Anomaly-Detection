# Docker Commands Reference

# Stock Anomaly Detection Project

## 📋 Table of Contents

- [Starting the Application](#-starting-the-application)
- [Stopping the Application](#-stopping-the-application)
- [Viewing Logs](#-viewing-logs)
- [Container Management](#-container-management)
- [Database Operations](#-database-operations)
- [Data Ingestion](#-data-ingestion)
- [Building & Rebuilding](#-building--rebuilding)
- [Monitoring Stack](#-monitoring-stack)
- [Cleanup & Reset](#-cleanup--reset)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Starting the Application

### Start all services (detached mode)

```powershell
docker-compose up -d
```

### Start all services with live logs

```powershell
docker-compose up
```

### Start specific service only

```powershell
docker-compose up -d database      # Database only
docker-compose up -d backend       # Backend only
docker-compose up -d frontend      # Frontend only
```

### Start with rebuild

```powershell
docker-compose up -d --build
```

---

## 🛑 Stopping the Application

### Stop all services (keeps volumes)

```powershell
docker-compose down
```

### Stop all services and remove volumes (⚠️ deletes data)

```powershell
docker-compose down -v
```

### Stop specific service

```powershell
docker-compose stop backend
docker-compose stop frontend
docker-compose stop database
```

---

## 📜 Viewing Logs

### View all logs (live)

```powershell
docker-compose logs -f
```

### View specific service logs

```powershell
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### View last N lines

```powershell
docker-compose logs --tail 50 backend
docker-compose logs --tail 100 database
```

### View logs with timestamps

```powershell
docker-compose logs -f -t backend
```

---

## 🐳 Container Management

### List running containers

```powershell
docker ps
docker-compose ps
```

### List all containers (including stopped)

```powershell
docker ps -a
```

### Check container status

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Restart a service

```powershell
docker-compose restart backend
docker-compose restart frontend
docker-compose restart database
```

### Execute command inside container

```powershell
docker exec -it anomaly-backend bash
docker exec -it anomaly-frontend sh
docker exec -it anomaly-db psql -U stockuser -d stock_db
```

### View container resource usage

```powershell
docker stats
```

---

## 🗄️ Database Operations

### Connect to PostgreSQL

```powershell
docker exec -it anomaly-db psql -U stockuser -d stock_db
```

### Run SQL query directly

```powershell
docker exec anomaly-db psql -U stockuser -d stock_db -c "SELECT * FROM stocks;"
docker exec anomaly-db psql -U stockuser -d stock_db -c "SELECT COUNT(*) FROM stock_prices;"
docker exec anomaly-db psql -U stockuser -d stock_db -c "SELECT COUNT(*) FROM anomalies;"
```

### List all tables

```powershell
docker exec anomaly-db psql -U stockuser -d stock_db -c "\dt"
```

### Describe a table

```powershell
docker exec anomaly-db psql -U stockuser -d stock_db -c "\d stocks"
docker exec anomaly-db psql -U stockuser -d stock_db -c "\d stock_prices"
docker exec anomaly-db psql -U stockuser -d stock_db -c "\d anomalies"
```

### Backup database

```powershell
docker exec anomaly-db pg_dump -U stockuser stock_db > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

### Restore database

```powershell
Get-Content backup.sql | docker exec -i anomaly-db psql -U stockuser -d stock_db
```

---

## 📊 Data Ingestion

### Add sample stocks to database

```powershell
docker exec anomaly-backend python add_sample_data.py
```

### Fetch historical stock data (3 years)

```powershell
docker exec anomaly-backend python data_collection/fetch_historical_data.py
```

### Run both (full data setup)

```powershell
docker exec anomaly-backend python add_sample_data.py
docker exec anomaly-backend python data_collection/fetch_historical_data.py
```

---

## 🔨 Building & Rebuilding

### Rebuild all images

```powershell
docker-compose build
```

### Rebuild specific service

```powershell
docker-compose build backend
docker-compose build frontend
```

### Rebuild without cache

```powershell
docker-compose build --no-cache
docker-compose build --no-cache backend
```

### Rebuild and start

```powershell
docker-compose up -d --build
docker-compose up -d --build backend
```

---

## 📈 Monitoring Stack (Optional)

### Start with monitoring (Prometheus + Grafana)

```powershell
docker-compose --profile monitoring up -d
```

### Stop monitoring stack

```powershell
docker-compose --profile monitoring down
```

### Access URLs (when monitoring is enabled)

# Prometheus: http://localhost:9090

# Grafana: http://localhost:3001 (login: admin/admin)

---

## 🧹 Cleanup & Reset

### Remove stopped containers

```powershell
docker container prune
```

### Remove unused images

```powershell
docker image prune
```

### Remove unused volumes (⚠️ caution)

```powershell
docker volume prune
```

### Full cleanup (⚠️ removes all project data)

```powershell
docker-compose down -v --rmi all
```

### Reset database only

```powershell
docker-compose stop database
docker volume rm anomaly-detection_postgres_data
docker-compose up -d database
```

### Complete project reset

```powershell
docker-compose down -v
docker-compose up -d --build
docker exec anomaly-backend python add_sample_data.py
docker exec anomaly-backend python data_collection/fetch_historical_data.py
```

---

## 🔧 Troubleshooting

### Check if services are healthy

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Check backend health endpoint

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" | ConvertTo-Json
```

### Check frontend is accessible

```powershell
(Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing).StatusCode
```

### View container inspect details

```powershell
docker inspect anomaly-backend
docker inspect anomaly-frontend
docker inspect anomaly-db
```

### Check volume details

```powershell
docker volume ls --filter "name=anomaly"
docker volume inspect anomaly-detection_postgres_data
```

### Check network

```powershell
docker network ls --filter "name=anomaly"
docker network inspect anomaly-detection_anomaly-network
```

### Force recreate containers

```powershell
docker-compose up -d --force-recreate
```

### View Docker system info

```powershell
docker system df
docker system info
```

---

## 🌐 Service URLs

| Service     | URL                        | Description                     |
| ----------- | -------------------------- | ------------------------------- |
| Frontend    | http://localhost:3000      | Web Dashboard                   |
| Backend API | http://localhost:8000      | REST API                        |
| API Docs    | http://localhost:8000/docs | Swagger UI                      |
| Database    | localhost:5432             | PostgreSQL                      |
| Prometheus  | http://localhost:9090      | Metrics (monitoring profile)    |
| Grafana     | http://localhost:3001      | Dashboards (monitoring profile) |

---

## 🔐 Default Credentials

### Database

- **User:** `stockuser`
- **Password:** `stockpassword`
- **Database:** `stock_db`

### Grafana (when monitoring enabled)

- **User:** `admin`
- **Password:** `admin`

### To use custom credentials

Create a `.env` file in project root:

```env
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
GRAFANA_USER=your_grafana_user
GRAFANA_PASSWORD=your_grafana_password
```

---

## 📝 Quick Reference

```powershell
# Start everything
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f

# Ingest data
docker exec anomaly-backend python add_sample_data.py
docker exec anomaly-backend python data_collection/fetch_historical_data.py

# Stop everything
docker-compose down

# Full reset
docker-compose down -v && docker-compose up -d --build
```
