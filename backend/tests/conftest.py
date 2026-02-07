"""
Pytest configuration and shared fixtures for anomaly detection tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os


@pytest.fixture
def sample_stock_data():
    """
    Generate realistic sample stock data for testing.
    
    Returns:
        pd.DataFrame with columns: date, open, high, low, close, volume
    """
    np.random.seed(42)
    n_days = 100
    
    # Generate dates
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    # Generate realistic stock prices with trend and volatility
    base_price = 150.0
    returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
    prices = base_price * np.cumprod(1 + returns)
    
    # Generate OHLC data
    daily_range = np.abs(np.random.normal(0.02, 0.01, n_days))
    high = prices * (1 + daily_range / 2)
    low = prices * (1 - daily_range / 2)
    open_price = low + np.random.random(n_days) * (high - low)
    
    # Generate volume
    base_volume = 50_000_000
    volume = np.random.normal(base_volume, base_volume * 0.3, n_days).astype(int)
    volume = np.clip(volume, 10_000_000, None)
    
    return pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    })


@pytest.fixture
def sample_stock_data_with_anomalies(sample_stock_data):
    """
    Generate stock data with injected anomalies for testing detection.
    
    Returns:
        Tuple of (DataFrame, list of anomaly indices)
    """
    df = sample_stock_data.copy()
    anomaly_indices = []
    
    # Inject price spike anomaly
    spike_idx = 25
    df.loc[spike_idx, 'close'] *= 1.15  # 15% spike
    df.loc[spike_idx, 'high'] *= 1.18
    anomaly_indices.append(spike_idx)
    
    # Inject price drop anomaly
    drop_idx = 50
    df.loc[drop_idx, 'close'] *= 0.85  # 15% drop
    df.loc[drop_idx, 'low'] *= 0.82
    anomaly_indices.append(drop_idx)
    
    # Inject volume anomaly
    vol_idx = 75
    df.loc[vol_idx, 'volume'] *= 5  # 5x volume spike
    anomaly_indices.append(vol_idx)
    
    return df, anomaly_indices


@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model storage during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def small_stock_data():
    """
    Generate minimal stock data for quick tests.
    
    Returns:
        pd.DataFrame with 30 rows
    """
    np.random.seed(42)
    n_days = 30
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    base_price = 100.0
    prices = base_price + np.cumsum(np.random.normal(0, 1, n_days))
    
    return pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1_000_000, 10_000_000, n_days)
    })


@pytest.fixture
def mock_model_metadata():
    """Create mock model metadata for testing."""
    return {
        'model_type': 'isolation_forest',
        'symbol': 'TEST',
        'trained_at': datetime.utcnow().isoformat(),
        'data_hash': 'abc123def456',
        'hyperparameters': {
            'contamination': 0.1,
            'n_estimators': 100
        },
        'metrics': {
            'precision': 0.85,
            'recall': 0.80,
            'f1_score': 0.82
        }
    }
