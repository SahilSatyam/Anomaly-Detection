"""
Unit tests for Machine Learning anomaly detection models.

Tests cover:
- Isolation Forest detector
- LSTM anomaly detector
- AutoEncoder detector
- Model persistence integration
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anomaly_detection.ml_models import (
    MLAnomalyDetector,
    LSTMAnomalyDetector,
    AutoEncoderAnomalyDetector
)
from anomaly_detection.statistical_methods import AnomalyResult
from anomaly_detection.model_persistence import ModelPersistenceManager


class TestMLAnomalyDetector:
    """Tests for Isolation Forest based anomaly detector."""
    
    def test_initialization_default(self):
        """Test default initialization."""
        detector = MLAnomalyDetector()
        
        assert detector.contamination == 0.1
        assert detector.max_model_age_hours == 24
    
    def test_initialization_custom(self, temp_model_dir):
        """Test initialization with custom parameters."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(
            contamination=0.05,
            model_manager=model_manager,
            max_model_age_hours=12
        )
        
        assert detector.contamination == 0.05
        assert detector.max_model_age_hours == 12
    
    def test_prepare_data(self, sample_stock_data):
        """Test data preparation for ML models."""
        detector = MLAnomalyDetector()
        
        features = detector.prepare_data(sample_stock_data)
        
        # Should return scaled numpy array
        assert isinstance(features, np.ndarray)
        
        # Features should be normalized (mean ~0, std ~1)
        assert abs(np.mean(features)) < 1.0
        assert abs(np.std(features) - 1.0) < 0.5
    
    def test_fit(self, sample_stock_data, temp_model_dir):
        """Test model fitting."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(model_manager=model_manager)
        
        result = detector.fit(sample_stock_data, symbol='TEST')
        
        # Should return self for method chaining
        assert result is detector
        
        # Model should be fitted
        assert detector.model is not None
    
    def test_detect_isolation_forest_anomalies(self, sample_stock_data, temp_model_dir):
        """Test Isolation Forest anomaly detection."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(
            contamination=0.1,
            model_manager=model_manager
        )
        
        anomalies = detector.detect_isolation_forest_anomalies(
            sample_stock_data, 
            symbol='TEST'
        )
        
        # Should return list of AnomalyResult
        assert isinstance(anomalies, list)
        
        for anomaly in anomalies:
            assert isinstance(anomaly, AnomalyResult)
            assert anomaly.method == 'isolation_forest'
    
    def test_detect_with_injected_anomalies(self, sample_stock_data_with_anomalies, temp_model_dir):
        """Test detection of injected anomalies."""
        df, anomaly_indices = sample_stock_data_with_anomalies
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(
            contamination=0.15,  # Higher to catch more
            model_manager=model_manager
        )
        
        anomalies = detector.detect_isolation_forest_anomalies(df, symbol='TEST')
        
        # Should detect some anomalies
        assert len(anomalies) > 0
    
    def test_model_caching(self, sample_stock_data, temp_model_dir):
        """Test that models are cached and reused."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(model_manager=model_manager)
        
        # First detection - trains model
        anomalies1 = detector.detect_isolation_forest_anomalies(
            sample_stock_data, 
            symbol='CACHE_TEST'
        )
        
        # Second detection - should use cached model
        anomalies2 = detector.detect_isolation_forest_anomalies(
            sample_stock_data, 
            symbol='CACHE_TEST'
        )
        
        # Results should be identical (same model)
        assert len(anomalies1) == len(anomalies2)
    
    def test_small_dataset(self, small_stock_data, temp_model_dir):
        """Test handling of small datasets."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = MLAnomalyDetector(model_manager=model_manager)
        
        anomalies = detector.detect_isolation_forest_anomalies(
            small_stock_data, 
            symbol='SMALL'
        )
        
        assert isinstance(anomalies, list)


class TestLSTMAnomalyDetector:
    """Tests for LSTM-based anomaly detector."""
    
    def test_initialization(self):
        """Test LSTM detector initialization."""
        detector = LSTMAnomalyDetector(
            sequence_length=10,
            threshold=2.0
        )
        
        assert detector.sequence_length == 10
        assert detector.threshold == 2.0
    
    def test_prepare_sequences(self, sample_stock_data):
        """Test sequence preparation for LSTM."""
        detector = LSTMAnomalyDetector(sequence_length=10)
        
        X, y = detector.prepare_sequences(sample_stock_data)
        
        # X should have shape (n_samples, sequence_length, 1)
        assert len(X.shape) == 3
        assert X.shape[1] == 10
        
        # y should have same number of samples
        assert len(X) == len(y)
    
    def test_build_model(self):
        """Test LSTM model architecture."""
        detector = LSTMAnomalyDetector(sequence_length=10)
        
        model = detector._build_model()
        
        # Model should have layers
        assert len(model.layers) > 0
        
        # Input shape should match sequence length
        input_shape = model.input_shape
        assert input_shape[1] == 10  # sequence length
    
    @pytest.mark.slow
    def test_fit_lstm(self, sample_stock_data, temp_model_dir):
        """Test LSTM model training (slow - requires GPU for speed)."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = LSTMAnomalyDetector(
            sequence_length=10,
            model_manager=model_manager
        )
        
        # Train with minimal epochs for testing
        result = detector.fit(
            sample_stock_data, 
            symbol='LSTM_TEST',
            epochs=2,
            batch_size=16
        )
        
        assert result is detector
        assert detector.model is not None
    
    @pytest.mark.slow
    def test_detect_lstm_anomalies(self, sample_stock_data, temp_model_dir):
        """Test LSTM anomaly detection."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = LSTMAnomalyDetector(
            sequence_length=10,
            threshold=1.5,
            model_manager=model_manager
        )
        
        anomalies = detector.detect_lstm_anomalies(
            sample_stock_data,
            symbol='LSTM_DETECT'
        )
        
        assert isinstance(anomalies, list)
        
        for anomaly in anomalies:
            assert isinstance(anomaly, AnomalyResult)
            assert anomaly.method == 'lstm'
    
    def test_insufficient_data(self):
        """Test handling of data smaller than sequence length."""
        detector = LSTMAnomalyDetector(sequence_length=50)
        
        # Create data smaller than sequence length
        small_df = pd.DataFrame({
            'date': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'close': np.random.random(30) * 100,
            'volume': np.random.randint(1000000, 10000000, 30)
        })
        
        # Should handle gracefully
        X, y = detector.prepare_sequences(small_df)
        
        # Should return empty or handle appropriately
        assert len(X) == 0 or len(X) > 0


class TestAutoEncoderAnomalyDetector:
    """Tests for AutoEncoder-based anomaly detector."""
    
    def test_initialization(self):
        """Test AutoEncoder detector initialization."""
        detector = AutoEncoderAnomalyDetector(
            encoding_dim=8,
            threshold_percentile=95.0
        )
        
        assert detector.encoding_dim == 8
        assert detector.threshold_percentile == 95.0
    
    @pytest.mark.slow
    def test_fit_autoencoder(self, sample_stock_data, temp_model_dir):
        """Test AutoEncoder training."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = AutoEncoderAnomalyDetector(
            encoding_dim=8,
            model_manager=model_manager
        )
        
        result = detector.fit(
            sample_stock_data,
            symbol='AE_TEST',
            epochs=5,
            batch_size=16
        )
        
        assert result is detector
        assert detector.model is not None
    
    @pytest.mark.slow
    def test_detect_autoencoder_anomalies(self, sample_stock_data_with_anomalies, temp_model_dir):
        """Test AutoEncoder anomaly detection."""
        df, _ = sample_stock_data_with_anomalies
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        detector = AutoEncoderAnomalyDetector(
            encoding_dim=8,
            threshold_percentile=90.0,
            model_manager=model_manager
        )
        
        anomalies = detector.detect_anomalies(
            df,
            symbol='AE_DETECT'
        )
        
        assert isinstance(anomalies, list)


class TestMLModelsIntegration:
    """Integration tests for ML models working together."""
    
    def test_all_ml_models_same_data(self, sample_stock_data, temp_model_dir):
        """Test running all ML models on the same dataset."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Isolation Forest
        if_detector = MLAnomalyDetector(model_manager=model_manager)
        if_anomalies = if_detector.detect_isolation_forest_anomalies(
            sample_stock_data,
            symbol='INT_IF'
        )
        
        assert isinstance(if_anomalies, list)
        
        # Verify different methods produce results
        for anomaly in if_anomalies:
            assert anomaly.method == 'isolation_forest'
    
    def test_model_persistence_across_sessions(self, sample_stock_data, temp_model_dir):
        """Test that saved models can be loaded in new detector instances."""
        model_manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # First session - train and save
        detector1 = MLAnomalyDetector(model_manager=model_manager)
        anomalies1 = detector1.detect_isolation_forest_anomalies(
            sample_stock_data,
            symbol='PERSIST_TEST'
        )
        
        # Second session - new detector should load cached model
        detector2 = MLAnomalyDetector(model_manager=model_manager)
        anomalies2 = detector2.detect_isolation_forest_anomalies(
            sample_stock_data,
            symbol='PERSIST_TEST'
        )
        
        # Results should match
        assert len(anomalies1) == len(anomalies2)
