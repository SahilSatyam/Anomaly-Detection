# 📚 Stock Anomaly Detection - Documentation

Welcome to the documentation for the Stock Anomaly Detection System.

---

## 📖 Documentation Index

| Document                                                       | Description                                       |
| -------------------------------------------------------------- | ------------------------------------------------- |
| [Main README](../README.md)                                    | Project overview, features, and quick start guide |
| [Backend README](../backend/README.md)                         | API endpoints, backend setup, and configuration   |
| [DEVOPS Guide](../DEVOPS.md)                                   | Docker, CI/CD, monitoring, and deployment         |
| [Model Retraining Pipeline](MODEL_RETRAINING_PIPELINE.md)      | MLOps, automated retraining, and model versioning |
| [Start Project Workflow](../.agent/workflows/start-project.md) | Step-by-step project setup instructions           |

---

## 🧪 Testing Documentation

The project includes a comprehensive test suite:

| Test Category       | Location                                    | Description                                |
| ------------------- | ------------------------------------------- | ------------------------------------------ |
| Statistical Methods | `backend/tests/test_statistical_methods.py` | Bollinger Bands, Z-Score, Volume detection |
| ML Models           | `backend/tests/test_ml_models.py`           | Isolation Forest, LSTM, AutoEncoder        |
| Model Persistence   | `backend/tests/test_model_persistence.py`   | Caching, versioning, expiration            |
| API Endpoints       | `backend/tests/test_api_endpoints.py`       | REST API, validation, error handling       |
| Fixtures            | `backend/tests/conftest.py`                 | Shared test fixtures and sample data       |

### Running Tests

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest --cov=anomaly_detection --cov-report=html

# Skip slow tests (ML training)
pytest -m "not slow" -v
```

---

## 📓 Jupyter Notebooks

| Notebook                                                           | Description                                   | Recommended Platform |
| ------------------------------------------------------------------ | --------------------------------------------- | -------------------- |
| [GPU Training](../notebooks/GPU_Training_Colab.ipynb)              | Train advanced models (Transformer, VAE, TCN) | Google Colab (GPU)   |
| [Model Evaluation](../notebooks/Model_Evaluation_Benchmarks.ipynb) | Evaluate and benchmark all detection methods  | Local or Colab       |

---

## 🏗️ Architecture Overview

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
│                                                              │
│  Detection Methods:                                          │
│  • Statistical: Bollinger Bands, Z-Score, Volume            │
│  • ML: Isolation Forest, LSTM, AutoEncoder                  │
│  • Advanced DL: Transformer, VAE, TCN                       │
│  • Forecasting: ARIMA, Prophet                              │
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

## 📊 API Quick Reference

| Category  | Endpoint                      | Method   | Description            |
| --------- | ----------------------------- | -------- | ---------------------- |
| Health    | `/api/health`                 | GET      | Health check           |
| Health    | `/api/ready`                  | GET      | Readiness check        |
| Stocks    | `/api/stocks`                 | GET      | List all stocks        |
| Stocks    | `/api/stock-data`             | GET      | Get historical prices  |
| Anomalies | `/api/anomalies`              | GET      | Get detected anomalies |
| Anomalies | `/api/detect-anomalies`       | POST     | Trigger detection      |
| Models    | `/api/models`                 | GET      | List cached ML models  |
| Models    | `/api/models/{type}/{symbol}` | DELETE   | Delete cached model    |
| Alerts    | `/api/alerts/status`          | GET      | Alert system status    |
| Settings  | `/api/settings`               | GET/POST | Get/update settings    |
| Metrics   | `/metrics`                    | GET      | Prometheus metrics     |

Full API documentation: http://localhost:8000/docs

---

## 📅 Last Updated

**January 2026** - Added comprehensive test suite, model evaluation notebooks, and MLOps documentation.
