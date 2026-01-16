# 📈 Stock Anomaly Detection System

A full-stack application for real-time stock market monitoring, anomaly detection, and alerting. Uses advanced ML algorithms including LSTM neural networks, Isolation Forest, and time-series forecasting to detect unusual patterns in stock price movements.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![React](https://img.shields.io/badge/React-19.x-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 🔍 Anomaly Detection

- **Statistical Methods**: Bollinger Bands, Z-Score, Volume Analysis
- **Machine Learning**: Isolation Forest, LSTM Neural Networks, AutoEncoder
- **Time-Series Forecasting**: ARIMA (auto-tuned), Facebook Prophet
- **Hybrid Detection**: Consensus-based multi-method analysis

### 📊 Visualization

- Interactive candlestick charts with volume overlay
- Anomaly markers directly on price charts
- Severity-based color coding (high/medium/low)
- Real-time data updates with auto-refresh

### 🚨 Alert System

- Email notifications (SMTP)
- Slack/Discord webhooks
- Custom webhook support
- Configurable severity thresholds

### ⚡ Performance

- Model caching to avoid retraining
- Database query optimization with indexes
- Pagination for large datasets
- Background data collection

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/SahilSatyam/Anomaly-Detection.git
cd Anomaly-Detection

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

**Access:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL (optional)
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local

# Start development server
npm start
```

---

## 📁 Project Structure

```
Anomaly-Detection/
├── backend/                    # FastAPI Backend
│   ├── main.py                # API endpoints
│   ├── data_collection/       # Stock data fetching
│   ├── data_storage/          # Database models & operations
│   ├── anomaly_detection/     # Detection algorithms
│   │   ├── statistical_methods.py
│   │   ├── ml_models.py       # LSTM, Isolation Forest
│   │   ├── forecasting.py     # ARIMA, Prophet
│   │   └── model_persistence.py
│   ├── alert_system/          # Email & webhook alerts
│   ├── alembic/               # Database migrations
│   └── Dockerfile
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Dashboard, Settings
│   │   ├── hooks/             # Custom React hooks
│   │   ├── utils/             # Utilities (export, validation)
│   │   └── config/            # API configuration
│   ├── nginx.conf             # Production config
│   └── Dockerfile
│
├── monitoring/                 # Prometheus configs
├── database/                   # Init scripts
├── .github/workflows/          # CI/CD pipelines
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Development commands
└── DEVOPS.md                   # Deployment guide
```

---

## 🔌 API Endpoints

### Stock Data

| Method | Endpoint          | Description             |
| ------ | ----------------- | ----------------------- |
| GET    | `/api/stocks`     | List all tracked stocks |
| GET    | `/api/stock-data` | Get historical prices   |

### Anomaly Detection

| Method | Endpoint                | Description             |
| ------ | ----------------------- | ----------------------- |
| GET    | `/api/anomalies`        | Get detected anomalies  |
| POST   | `/api/detect-anomalies` | Trigger detection       |
| GET    | `/api/detection/status` | Detection system status |

### Models & Alerts

| Method | Endpoint                      | Description           |
| ------ | ----------------------------- | --------------------- |
| GET    | `/api/models`                 | List cached ML models |
| DELETE | `/api/models/{type}/{symbol}` | Delete cached model   |
| GET    | `/api/alerts/status`          | Alert system status   |
| GET    | `/api/alerts/history`         | Alert history         |

### System

| Method | Endpoint      | Description        |
| ------ | ------------- | ------------------ |
| GET    | `/api/health` | Health check       |
| GET    | `/api/ready`  | Readiness check    |
| GET    | `/metrics`    | Prometheus metrics |

Full API documentation at http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

| Variable              | Description              | Default                 |
| --------------------- | ------------------------ | ----------------------- |
| `DATABASE_URL`        | PostgreSQL connection    | Required                |
| `LOG_LEVEL`           | Logging level            | `INFO`                  |
| `LOG_FORMAT`          | `json` or `text`         | `text`                  |
| `ALERT_EMAIL_ENABLED` | Enable email alerts      | `false`                 |
| `SLACK_WEBHOOK_URL`   | Slack notifications      | -                       |
| `DISCORD_WEBHOOK_URL` | Discord notifications    | -                       |
| `REACT_APP_API_URL`   | Backend URL for frontend | `http://localhost:8000` |

See `.env.example` for all available options.

---

## 🧪 Testing

```bash
# Run all tests
make test

# Backend only
cd backend && pytest -v --cov=.

# Frontend only
cd frontend && npm test -- --coverage
```

---

## 📦 Deployment

### Docker Compose (Production)

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Scale backend
docker-compose up -d --scale backend=3
```

### CI/CD

GitHub Actions pipeline includes:

- Automated testing on push/PR
- Docker image building
- Security scanning (Trivy)
- Container registry push

See `.github/workflows/ci-cd.yml`

### Database Migrations

```bash
# Apply migrations
cd backend && alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

---

## 📊 Monitoring

### Prometheus Metrics

Enable with: `docker-compose --profile monitoring up -d`

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

Available metrics:

- `http_requests_total` - Request counts
- `http_request_duration_seconds` - Latency
- `anomaly_detection_runs_total` - Detection runs
- `model_cache_hits_total` - Cache efficiency

---

## 🛠️ Development

### Makefile Commands

```bash
make help        # Show all commands
make install     # Install dependencies
make dev         # Start development servers
make test        # Run all tests
make lint        # Run linters
make docker-up   # Start Docker containers
make migrate     # Run database migrations
```

### Adding New Detection Methods

1. Create detector class in `backend/anomaly_detection/`
2. Implement `detect()` method returning `List[AnomalyResult]`
3. Register in `__init__.py`
4. Add to `/api/detect-anomalies` endpoint

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📧 Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/SahilSatyam/Anomaly-Detection/issues) page.
