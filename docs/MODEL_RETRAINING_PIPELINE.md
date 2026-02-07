# Model Retraining Pipeline Documentation

This document outlines the model retraining strategy and MLOps practices for the Stock Anomaly Detection System.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Retraining Triggers](#retraining-triggers)
3. [Pipeline Architecture](#pipeline-architecture)
4. [Automated Retraining](#automated-retraining)
5. [Manual Retraining](#manual-retraining)
6. [Model Versioning](#model-versioning)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Best Practices](#best-practices)

---

## Overview

The model retraining pipeline ensures anomaly detection models remain accurate as market conditions change. It supports:

- **Automatic retraining** based on model age and data drift
- **Scheduled retraining** via cron jobs
- **Manual retraining** via API endpoints
- **Model versioning** with metadata tracking

---

## Retraining Triggers

### 1. Time-Based Expiration

Models are automatically invalidated after a configurable period (default: 24 hours).

```python
# Configuration in model_persistence.py
max_model_age_hours = 24  # Model expires after 24 hours
```

### 2. Data Drift Detection

Models are retrained when the training data hash changes:

```python
from anomaly_detection.model_persistence import ModelPersistenceManager

manager = ModelPersistenceManager()
current_hash = manager.compute_data_hash(new_data)

# If hash differs from stored hash, model is retrained
```

### 3. Performance Degradation

Monitor model performance and trigger retraining when metrics drop:

| Metric              | Threshold | Action           |
| ------------------- | --------- | ---------------- |
| Precision           | < 0.70    | Retrain          |
| Recall              | < 0.60    | Retrain          |
| F1-Score            | < 0.65    | Alert + Retrain  |
| False Positive Rate | > 0.30    | Adjust threshold |

### 4. Manual Trigger

Retrain via API or command line when needed:

```bash
# Via API
curl -X POST http://localhost:8000/api/models/retrain \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "model_type": "lstm"}'

# Via command line
python -c "from scripts.retrain import retrain_model; retrain_model('AAPL', 'lstm')"
```

---

## Pipeline Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Data Source   │────▶│  Data Pipeline   │────▶│  Feature Store  │
│   (YFinance)    │     │  (Collection)    │     │  (PostgreSQL)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        │                                 ▼                                 │
                        │  ┌──────────────────┐     ┌──────────────┐     ┌──────────────┐  │
                        │  │   Model Cache    │◀────│   Training   │◀────│   Trigger    │  │
                        │  │   (./models/)    │     │   Pipeline   │     │   Service    │  │
                        │  └────────┬─────────┘     └──────────────┘     └──────────────┘  │
                        │           │                                                       │
                        │           ▼                                                       │
                        │  ┌──────────────────┐     ┌──────────────┐     ┌──────────────┐  │
                        │  │    Inference     │────▶│   Results    │────▶│    Alerts    │  │
                        │  │    Service       │     │   Storage    │     │    System    │  │
                        │  └──────────────────┘     └──────────────┘     └──────────────┘  │
                        │                                                                   │
                        │                         MLOps Pipeline                            │
                        └───────────────────────────────────────────────────────────────────┘
```

---

## Automated Retraining

### Scheduled Retraining (Cron)

Add to crontab for regular retraining:

```bash
# Retrain all models daily at 2 AM
0 2 * * * cd /path/to/backend && python scripts/scheduled_retrain.py

# Cleanup expired models weekly
0 3 * * 0 cd /path/to/backend && python scripts/cleanup_models.py
```

### Retraining Script

Create `backend/scripts/scheduled_retrain.py`:

```python
#!/usr/bin/env python
"""Scheduled model retraining script."""

import logging
from datetime import datetime
from anomaly_detection.model_persistence import ModelPersistenceManager
from anomaly_detection.ml_models import MLAnomalyDetector, LSTMAnomalyDetector
from data_collection.stock_data import get_historical_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
MODELS = ['isolation_forest', 'lstm']

def retrain_all_models():
    """Retrain all models for all symbols."""
    manager = ModelPersistenceManager()
    results = []

    for symbol in SYMBOLS:
        logger.info(f"Processing {symbol}...")

        # Fetch fresh data
        data = get_historical_data(symbol, days=365)

        if data is None or len(data) < 100:
            logger.warning(f"Insufficient data for {symbol}")
            continue

        for model_type in MODELS:
            try:
                # Delete existing model
                manager.delete_model(model_type, symbol)

                # Retrain based on model type
                if model_type == 'isolation_forest':
                    detector = MLAnomalyDetector(model_manager=manager)
                    detector.fit(data, symbol=symbol)
                elif model_type == 'lstm':
                    detector = LSTMAnomalyDetector(model_manager=manager)
                    detector.fit(data, symbol=symbol, epochs=50)

                results.append({
                    'symbol': symbol,
                    'model': model_type,
                    'status': 'success',
                    'timestamp': datetime.utcnow()
                })
                logger.info(f"  ✓ Retrained {model_type} for {symbol}")

            except Exception as e:
                logger.error(f"  ✗ Failed {model_type} for {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'model': model_type,
                    'status': 'failed',
                    'error': str(e)
                })

    return results

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"SCHEDULED MODEL RETRAINING - {datetime.now()}")
    print('='*60)

    results = retrain_all_models()

    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')

    print(f"\n✓ Completed: {success} models retrained, {failed} failed")
```

---

## Manual Retraining

### Via Python

```python
from anomaly_detection.model_persistence import ModelPersistenceManager
from anomaly_detection.ml_models import MLAnomalyDetector

# Initialize
manager = ModelPersistenceManager()

# Delete old model (optional)
manager.delete_model('isolation_forest', 'AAPL')

# Retrain
detector = MLAnomalyDetector(model_manager=manager)
detector.fit(stock_data, symbol='AAPL')
```

### Via API (Add to main.py)

```python
@app.post("/api/models/retrain")
async def retrain_model(request: RetrainRequest):
    """Manually trigger model retraining."""
    try:
        # Fetch fresh data
        data = await get_fresh_stock_data(request.symbol, days=365)

        # Delete existing model
        model_manager.delete_model(request.model_type, request.symbol)

        # Retrain
        if request.model_type == 'isolation_forest':
            detector = MLAnomalyDetector(model_manager=model_manager)
            detector.fit(data, symbol=request.symbol)
        elif request.model_type == 'lstm':
            detector = LSTMAnomalyDetector(model_manager=model_manager)
            detector.fit(data, symbol=request.symbol, epochs=50)

        return {"status": "success", "message": f"Retrained {request.model_type} for {request.symbol}"}
    except Exception as e:
        raise HTTPException(500, f"Retraining failed: {str(e)}")
```

---

## Model Versioning

### Metadata Storage

Each model stores metadata in JSON:

```json
{
  "model_type": "isolation_forest",
  "symbol": "AAPL",
  "trained_at": "2024-01-15T10:30:00Z",
  "data_hash": "a1b2c3d4e5f6",
  "hyperparameters": {
    "contamination": 0.1,
    "n_estimators": 100
  },
  "metrics": {
    "precision": 0.85,
    "recall": 0.78,
    "f1_score": 0.81,
    "training_samples": 365
  }
}
```

### Listing Models

```python
# List all cached models
from anomaly_detection.model_persistence import model_manager

models = model_manager.list_models()
for key, metadata in models.items():
    print(f"{key}: trained {metadata['trained_at']}, expired={metadata['is_expired']}")
```

---

## Monitoring & Alerting

### Prometheus Metrics

Track retraining in `metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge

# Retraining metrics
model_retrain_total = Counter(
    'model_retrain_total',
    'Total model retraining operations',
    ['model_type', 'symbol', 'status']
)

model_retrain_duration = Histogram(
    'model_retrain_duration_seconds',
    'Model retraining duration',
    ['model_type']
)

model_age_hours = Gauge(
    'model_age_hours',
    'Current age of cached model in hours',
    ['model_type', 'symbol']
)
```

### Alerting Rules

Add to Prometheus alerting rules:

```yaml
groups:
  - name: model_alerts
    rules:
      - alert: ModelRetrainingFailed
        expr: increase(model_retrain_total{status="failed"}[1h]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Model retraining failed"

      - alert: ModelTooOld
        expr: model_age_hours > 48
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Model is older than 48 hours"
```

---

## Best Practices

### 1. Retraining Schedule

| Model Type       | Recommended Frequency | Rationale                                 |
| ---------------- | --------------------- | ----------------------------------------- |
| Isolation Forest | Daily                 | Fast training, capture daily patterns     |
| LSTM             | Weekly                | Slower training, captures longer patterns |
| Transformer      | Weekly                | GPU-intensive, stable architecture        |
| Statistical      | No retraining         | Rule-based, no training needed            |

### 2. Data Requirements

- **Minimum samples**: 100 data points (ideally 365+ for daily data)
- **Data freshness**: Update source data before retraining
- **Data quality**: Validate for missing values, outliers

### 3. Validation Strategy

```python
def validate_retrained_model(model, validation_data, min_f1=0.6):
    """Validate model before deploying."""
    predictions = model.predict(validation_data)
    f1 = compute_f1_score(validation_data.labels, predictions)

    if f1 < min_f1:
        raise ValueError(f"Model F1 ({f1:.2f}) below threshold ({min_f1})")

    return True
```

### 4. Rollback Strategy

Keep previous model version for rollback:

```python
def save_with_backup(model, model_type, symbol):
    """Save model with backup of previous version."""
    backup_path = f"models/backup/{model_type}_{symbol}.joblib"
    current_path = f"models/{model_type}_{symbol}.joblib"

    # Backup existing
    if os.path.exists(current_path):
        shutil.copy(current_path, backup_path)

    # Save new
    joblib.dump(model, current_path)
```

---

## Quick Reference

### Commands

```bash
# Retrain specific model
python -c "from scripts.retrain import retrain_model; retrain_model('AAPL', 'lstm')"

# Cleanup expired models
python -c "from anomaly_detection.model_persistence import model_manager; model_manager.cleanup_expired(24)"

# List all models
python -c "from anomaly_detection.model_persistence import model_manager; print(model_manager.list_models())"

# Run tests
pytest tests/ -v --cov=anomaly_detection
```

### API Endpoints

| Endpoint                      | Method | Description            |
| ----------------------------- | ------ | ---------------------- |
| `/api/models`                 | GET    | List all cached models |
| `/api/models/{type}/{symbol}` | DELETE | Delete specific model  |
| `/api/models/retrain`         | POST   | Trigger retraining     |
| `/api/models/cleanup`         | POST   | Cleanup expired models |

---

## Changelog

| Version | Date       | Changes                                       |
| ------- | ---------- | --------------------------------------------- |
| 1.0.0   | 2024-01-15 | Initial documentation                         |
| 1.1.0   | 2024-06-01 | Added GPU training support                    |
| 1.2.0   | 2026-01-20 | Added Transformer models, enhanced monitoring |
