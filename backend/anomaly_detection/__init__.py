"""
Anomaly Detection Module

Provides multiple methods for detecting anomalies in stock price data:
- Statistical methods (Bollinger Bands, Z-Score)
- Machine Learning (Isolation Forest, LSTM, AutoEncoder)
- Time-series forecasting (ARIMA, Prophet)
- Hybrid detection combining multiple methods
"""

from .statistical_methods import StatisticalAnomalyDetector, AnomalyResult
from .ml_models import MLAnomalyDetector, LSTMAnomalyDetector, AutoEncoderAnomalyDetector
from .hybrid_detection import HybridAnomalyDetector
from .model_persistence import ModelPersistenceManager, model_manager

# Optional imports (may not be installed)
try:
    from .forecasting import ARIMAForecaster, ProphetForecaster, TrendAnalyzer
    FORECASTING_AVAILABLE = True
except ImportError:
    FORECASTING_AVAILABLE = False
    ARIMAForecaster = None
    ProphetForecaster = None
    TrendAnalyzer = None

__all__ = [
    # Core
    'AnomalyResult',
    'StatisticalAnomalyDetector',
    'MLAnomalyDetector',
    'LSTMAnomalyDetector',
    'AutoEncoderAnomalyDetector',
    'HybridAnomalyDetector',
    
    # Model persistence
    'ModelPersistenceManager',
    'model_manager',
    
    # Forecasting (optional)
    'ARIMAForecaster',
    'ProphetForecaster',
    'TrendAnalyzer',
    'FORECASTING_AVAILABLE'
]
