# Stock Anomaly Detection - Backend

FastAPI-based backend service for stock data collection, anomaly detection, and alerting.

## 🚀 Features

- **RESTful API** with OpenAPI documentation
- **Advanced Anomaly Detection**:
  - Statistical: Bollinger Bands, Z-Score, Volume Analysis
  - Machine Learning: Isolation Forest, LSTM, AutoEncoder
  - Advanced DL: Transformer, VAE, Temporal Convolutional Network
  - Time-Series: ARIMA (auto-tuned), Prophet
- **Model Persistence**: Cached ML models with automatic expiration
- **MLOps Pipeline**: Automated model retraining and versioning
- **Alert System**: Email, Slack, Discord, custom webhooks
- **Prometheus Metrics**: HTTP, database, and detection metrics
- **Structured Logging**: JSON format for log aggregation
- **Comprehensive Testing**: 80+ unit tests with coverage reporting

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- pip or Poetry

## 🛠️ Installation

### 1. Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

Required variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/stock_db
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Server

```bash
uvicorn main:app --reload --port 8000
```

API available at http://localhost:8000
Documentation at http://localhost:8000/docs

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI application & endpoints
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
│
├── data_collection/          # Stock data fetching
│   ├── fetch_data.py        # yfinance integration
│   └── scheduled_collector.py
│
├── data_storage/             # Database layer
│   ├── database.py          # DatabaseManager class
│   └── models.py            # SQLAlchemy models
│
├── anomaly_detection/        # Detection algorithms
│   ├── __init__.py          # Module exports
│   ├── statistical_methods.py # Bollinger, Z-Score
│   ├── ml_models.py         # Isolation Forest, LSTM, AutoEncoder
│   ├── advanced_models.py   # Transformer, VAE, TCN (GPU)
│   ├── forecasting.py       # ARIMA, Prophet
│   ├── hybrid_detection.py  # Consensus detection
│   └── model_persistence.py # Model caching
│
├── alert_system/             # Notifications
│   ├── __init__.py
│   ├── alert_manager.py     # Unified alert interface
│   ├── email_alerts.py      # SMTP integration
│   └── webhook_alerts.py    # Slack/Discord/custom
│
├── tests/                    # Unit & integration tests
│   ├── conftest.py          # Pytest fixtures & sample data
│   ├── test_statistical_methods.py
│   ├── test_ml_models.py
│   ├── test_model_persistence.py
│   └── test_api_endpoints.py
│
├── scripts/                  # Automation scripts
│   └── scheduled_retrain.py # Model retraining automation
│
├── alembic/                  # Database migrations
│   ├── env.py
│   └── versions/
│
├── logging_config.py         # Structured logging
├── metrics.py                # Prometheus metrics
├── pytest.ini                # Test configuration
└── Dockerfile               # Container image
```

## 🔌 API Endpoints

### Health & Monitoring

| Endpoint      | Method | Description        |
| ------------- | ------ | ------------------ |
| `/api/health` | GET    | Health check       |
| `/api/ready`  | GET    | Readiness check    |
| `/metrics`    | GET    | Prometheus metrics |

### Stock Data

| Endpoint          | Method | Description                   |
| ----------------- | ------ | ----------------------------- |
| `/api/stocks`     | GET    | List all stocks               |
| `/api/stocks`     | POST   | Add new stock                 |
| `/api/stock-data` | GET    | Historical prices (paginated) |

### Anomaly Detection

| Endpoint                | Method | Description                |
| ----------------------- | ------ | -------------------------- |
| `/api/anomalies`        | GET    | List anomalies (paginated) |
| `/api/anomalies/{id}`   | GET    | Get single anomaly         |
| `/api/anomalies/{id}`   | PUT    | Update anomaly             |
| `/api/anomalies/{id}`   | DELETE | Delete anomaly             |
| `/api/detect-anomalies` | POST   | Trigger detection          |
| `/api/detection/status` | GET    | Detection system status    |

### Model Management

| Endpoint                      | Method | Description            |
| ----------------------------- | ------ | ---------------------- |
| `/api/models`                 | GET    | List cached models     |
| `/api/models/{type}/{symbol}` | DELETE | Delete model           |
| `/api/models/cleanup`         | POST   | Cleanup expired models |

### Alerts

| Endpoint              | Method | Description         |
| --------------------- | ------ | ------------------- |
| `/api/alerts/status`  | GET    | Alert system status |
| `/api/alerts/history` | GET    | Recent alerts       |

### Settings

| Endpoint        | Method | Description     |
| --------------- | ------ | --------------- |
| `/api/settings` | GET    | Get settings    |
| `/api/settings` | POST   | Update settings |

## 📊 Detection API Example

```bash
curl -X POST http://localhost:8000/api/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "methods": ["all"],
    "save_to_database": true,
    "send_alerts": false,
    "lookback_days": 365,
    "threshold": 2.0
  }'
```

Response:

```json
{
  "symbol": "AAPL",
  "analysis_period": {
    "start": "2023-01-15",
    "end": "2024-01-15"
  },
  "total_anomalies": 12,
  "results_by_method": {
    "statistical": { "anomalies_count": 5 },
    "isolation_forest": { "anomalies_count": 3 },
    "lstm": { "anomalies_count": 4 }
  },
  "saved_to_database": 12,
  "alerts_sent": false,
  "processing_time_seconds": 2.45
}
```

## ⚙️ Configuration

### Environment Variables

| Variable                 | Description                      | Default  |
| ------------------------ | -------------------------------- | -------- |
| `DATABASE_URL`           | PostgreSQL connection string     | Required |
| `LOG_LEVEL`              | DEBUG, INFO, WARNING, ERROR      | `INFO`   |
| `LOG_FORMAT`             | `json` or `text`                 | `text`   |
| `ALERT_EMAIL_ENABLED`    | Enable email alerts              | `false`  |
| `SMTP_SERVER`            | SMTP server address              | -        |
| `SMTP_PORT`              | SMTP port                        | `587`    |
| `ALERT_EMAIL_SENDER`     | Sender email address             | -        |
| `ALERT_EMAIL_PASSWORD`   | Email password/app key           | -        |
| `ALERT_EMAIL_RECIPIENTS` | Comma-separated recipients       | -        |
| `SLACK_WEBHOOK_URL`      | Slack incoming webhook           | -        |
| `DISCORD_WEBHOOK_URL`    | Discord webhook                  | -        |
| `ALERT_MIN_SCORE`        | Minimum anomaly score for alerts | `1.5`    |

## 🗃️ Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new column"

# Rollback one migration
alembic downgrade -1

# View history
alembic history
```

## 📈 Monitoring

### Prometheus Metrics

Exposed at `/metrics`:

| Metric                            | Type      | Description         |
| --------------------------------- | --------- | ------------------- |
| `http_requests_total`             | Counter   | Total HTTP requests |
| `http_request_duration_seconds`   | Histogram | Request latency     |
| `db_queries_total`                | Counter   | Database queries    |
| `anomaly_detection_runs_total`    | Counter   | Detection runs      |
| `anomalies_detected_total`        | Counter   | Anomalies found     |
| `model_cache_hits_total`          | Counter   | Model cache hits    |
| `model_training_duration_seconds` | Histogram | Training time       |

### Structured Logging

Set `LOG_FORMAT=json` for structured logs:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "main",
  "message": "Detection complete for AAPL: 5 anomalies",
  "extra": {
    "symbol": "AAPL",
    "anomaly_count": 5,
    "duration_seconds": 2.45
  }
}
```

## 🧪 Testing

### Test Structure

| Test File                     | Coverage                             |
| ----------------------------- | ------------------------------------ |
| `test_statistical_methods.py` | Bollinger, Z-Score, Volume detection |
| `test_ml_models.py`           | Isolation Forest, LSTM, AutoEncoder  |
| `test_model_persistence.py`   | Caching, versioning, cleanup         |
| `test_api_endpoints.py`       | REST API, validation, errors         |

### Running Tests

```bash
# Run all tests with coverage
pytest -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ml_models.py -v

# Skip slow tests (LSTM/Transformer training)
pytest -m "not slow" -v

# Run with parallel execution
pytest -n auto -v
```

### Coverage Report

```bash
# Generate HTML report
pytest --cov=anomaly_detection --cov-report=html

# View report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

---

## 🔄 Model Retraining

### Automated Retraining

```bash
# Retrain all models
python scripts/scheduled_retrain.py --all

# Retrain specific model
python scripts/scheduled_retrain.py --symbol AAPL --model lstm

# Cleanup expired models
python scripts/scheduled_retrain.py --cleanup --max-age 24
```

### Scheduled Retraining (Cron)

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/backend && python scripts/scheduled_retrain.py --all
```

See [MODEL_RETRAINING_PIPELINE.md](../docs/MODEL_RETRAINING_PIPELINE.md) for full documentation.

## 🐳 Docker

```bash
# Build image
docker build -t anomaly-backend .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  anomaly-backend
```

## 📚 Adding New Detection Methods

1. Create detector module in `anomaly_detection/`:

```python
from dataclasses import dataclass
from typing import List
from .statistical_methods import AnomalyResult

class MyDetector:
    def detect(self, data, symbol: str) -> List[AnomalyResult]:
        anomalies = []
        # Your detection logic
        return anomalies
```

2. Export in `anomaly_detection/__init__.py`

3. Add to `/api/detect-anomalies` in `main.py`

## 📝 License

MIT License - see [LICENSE](../LICENSE)
