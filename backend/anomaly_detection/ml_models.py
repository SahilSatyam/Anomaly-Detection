"""
Machine Learning Anomaly Detection Models

Enhanced with model persistence to avoid retraining on every run.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import logging

from .statistical_methods import AnomalyResult
from .model_persistence import ModelPersistenceManager, model_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """
    Machine Learning based anomaly detector using Isolation Forest.
    
    Features:
    - Model persistence to disk
    - Automatic model caching and invalidation
    - Data change detection
    """
    
    def __init__(self, 
                 contamination: float = 0.1,
                 model_manager: Optional[ModelPersistenceManager] = None,
                 max_model_age_hours: int = 24):
        """
        Initialize the ML-based anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies in the data
            model_manager: Optional custom model manager
            max_model_age_hours: Maximum age of cached model before retraining
        """
        self.contamination = contamination
        self.model_manager = model_manager or globals()['model_manager']
        self.max_model_age_hours = max_model_age_hours
        
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        self.scaler = StandardScaler()
        self._is_fitted = False
        
    def prepare_data(self, data: pd.DataFrame) -> np.ndarray:
        """
        Prepare data for ML models.
        
        Args:
            data: DataFrame with price and volume data
            
        Returns:
            Scaled features array
        """
        features = data[['close', 'volume']].copy()
        features['returns'] = data['close'].pct_change()
        features['volume_change'] = data['volume'].pct_change()
        features = features.dropna()
        
        return self.scaler.fit_transform(features)
    
    def fit(self, data: pd.DataFrame, symbol: str = 'UNKNOWN') -> 'MLAnomalyDetector':
        """
        Fit the Isolation Forest model with caching.
        
        Args:
            data: Training data
            symbol: Stock symbol for model caching
            
        Returns:
            self for method chaining
        """
        # Compute data hash for change detection
        data_hash = self.model_manager.compute_data_hash(data)
        
        # Try to load cached model
        model, scaler, metadata = self.model_manager.load_sklearn_model(
            model_type='isolation_forest',
            symbol=symbol,
            data_hash=data_hash,
            max_age_hours=self.max_model_age_hours
        )
        
        if model is not None and scaler is not None:
            self.isolation_forest = model
            self.scaler = scaler
            self._is_fitted = True
            logger.info(f"Using cached Isolation Forest model for {symbol}")
            return self
        
        # Train new model
        logger.info(f"Training new Isolation Forest model for {symbol}")
        features = self.prepare_data(data)
        self.isolation_forest.fit(features)
        self._is_fitted = True
        
        # Save model
        self.model_manager.save_sklearn_model(
            model=self.isolation_forest,
            model_type='isolation_forest',
            symbol=symbol,
            data_hash=data_hash,
            hyperparameters={'contamination': self.contamination},
            scaler=self.scaler
        )
        
        return self

    def detect_isolation_forest_anomalies(self, data: pd.DataFrame, 
                                          symbol: str = 'UNKNOWN') -> List[AnomalyResult]:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            data: DataFrame with price and volume data
            symbol: Stock symbol for model caching
            
        Returns:
            List of detected anomalies
        """
        # Fit model if not already fitted
        if not self._is_fitted:
            self.fit(data, symbol)
        
        features = self.prepare_data(data)
        
        # Predict
        predictions = self.isolation_forest.predict(features)
        scores = self.isolation_forest.score_samples(features)
        
        anomalies = []
        for i in range(len(data)):
            if i < 1:  # Skip first row due to returns calculation
                continue
                
            if predictions[i-1] == -1:  # -1 indicates anomaly
                anomalies.append(AnomalyResult(
                    date=data['date'].iloc[i],
                    score=-scores[i-1],  # Negative score for anomalies
                    threshold=self.contamination,
                    is_anomaly=True,
                    method='isolation_forest',
                    details={
                        'price': float(data['close'].iloc[i]),
                        'volume': int(data['volume'].iloc[i]),
                        'returns': float(data['close'].pct_change().iloc[i]),
                        'volume_change': float(data['volume'].pct_change().iloc[i]),
                        'raw_score': float(scores[i-1])
                    }
                ))
                
        logger.info(f"Isolation Forest detected {len(anomalies)} anomalies for {symbol}")
        return anomalies


class LSTMAnomalyDetector:
    """
    LSTM-based anomaly detector with model persistence.
    
    Uses an autoencoder-style LSTM to predict the next price,
    and flags significant prediction errors as anomalies.
    """
    
    def __init__(self, 
                 sequence_length: int = 10, 
                 threshold: float = 2.0,
                 model_manager: Optional[ModelPersistenceManager] = None,
                 max_model_age_hours: int = 24):
        """
        Initialize the LSTM-based anomaly detector.
        
        Args:
            sequence_length: Number of time steps to use for prediction
            threshold: Threshold for anomaly detection (standard deviations)
            model_manager: Optional custom model manager
            max_model_age_hours: Maximum age of cached model before retraining
        """
        self.sequence_length = sequence_length
        self.threshold = threshold
        self.model_manager = model_manager or globals()['model_manager']
        self.max_model_age_hours = max_model_age_hours
        
        self.model = None
        self.scaler = StandardScaler()
        self._is_fitted = False
        
    def _build_model(self) -> Sequential:
        """
        Build LSTM model architecture.
        
        Returns:
            Compiled LSTM model
        """
        model = Sequential([
            LSTM(64, input_shape=(self.sequence_length, 1), return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        return model
        
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM model.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Tuple of X (sequences) and y (targets)
        """
        # Scale the data
        scaled_data = self.scaler.fit_transform(data[['close']].values)
        
        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length)])
            y.append(scaled_data[i + self.sequence_length])
            
        return np.array(X), np.array(y)
    
    def fit(self, data: pd.DataFrame, symbol: str = 'UNKNOWN',
            epochs: int = 50, batch_size: int = 32) -> 'LSTMAnomalyDetector':
        """
        Train the LSTM model with caching.
        
        Args:
            data: Training data
            symbol: Stock symbol for model caching
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            self for method chaining
        """
        # Compute data hash for change detection
        data_hash = self.model_manager.compute_data_hash(data)
        
        # Try to load cached model
        model, scaler, metadata = self.model_manager.load_keras_model(
            model_type='lstm',
            symbol=symbol,
            data_hash=data_hash,
            max_age_hours=self.max_model_age_hours
        )
        
        if model is not None:
            self.model = model
            if scaler is not None:
                self.scaler = scaler
            self._is_fitted = True
            logger.info(f"Using cached LSTM model for {symbol}")
            return self
        
        # Build and train new model
        logger.info(f"Training new LSTM model for {symbol}")
        self.model = self._build_model()
        
        X, y = self.prepare_sequences(data)
        
        # Train with early stopping
        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='loss',
            patience=5,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X, y, 
            epochs=epochs, 
            batch_size=batch_size, 
            verbose=0,
            callbacks=[early_stop]
        )
        
        self._is_fitted = True
        
        # Save model
        final_loss = history.history['loss'][-1]
        self.model_manager.save_keras_model(
            model=self.model,
            model_type='lstm',
            symbol=symbol,
            data_hash=data_hash,
            hyperparameters={
                'sequence_length': self.sequence_length,
                'threshold': self.threshold,
                'epochs': len(history.history['loss'])
            },
            scaler=self.scaler,
            metrics={'final_loss': final_loss}
        )
        
        logger.info(f"LSTM model trained for {symbol}, final loss: {final_loss:.6f}")
        return self
        
    def train(self, data: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> None:
        """
        Legacy training method for backward compatibility.
        
        Args:
            data: Training data
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        self.fit(data, 'UNKNOWN', epochs, batch_size)
        
    def detect_lstm_anomalies(self, data: pd.DataFrame,
                              symbol: str = 'UNKNOWN') -> List[AnomalyResult]:
        """
        Detect anomalies using LSTM predictions.
        
        Args:
            data: DataFrame with price data
            symbol: Stock symbol for model caching
            
        Returns:
            List of detected anomalies
        """
        # Fit model if not already fitted
        if not self._is_fitted or self.model is None:
            self.fit(data, symbol)
        
        X, y_true = self.prepare_sequences(data)
        y_pred = self.model.predict(X, verbose=0)
        
        # Calculate prediction errors
        errors = np.abs(y_true - y_pred)
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        
        anomalies = []
        for i in range(len(data) - self.sequence_length):
            error = errors[i][0]
            z_score = (error - mean_error) / (std_error + 1e-10)
            
            if z_score > self.threshold:
                anomalies.append(AnomalyResult(
                    date=data['date'].iloc[i + self.sequence_length],
                    score=float(z_score),
                    threshold=self.threshold,
                    is_anomaly=True,
                    method='lstm',
                    details={
                        'price': float(data['close'].iloc[i + self.sequence_length]),
                        'predicted_price': float(self.scaler.inverse_transform(y_pred[i].reshape(-1, 1))[0][0]),
                        'error': float(error),
                        'mean_error': float(mean_error),
                        'std_error': float(std_error)
                    }
                ))
        
        logger.info(f"LSTM detected {len(anomalies)} anomalies for {symbol}")
        return anomalies


class AutoEncoderAnomalyDetector:
    """
    AutoEncoder-based anomaly detector for multivariate time series.
    
    Uses a deep autoencoder to learn normal patterns,
    and flags high reconstruction errors as anomalies.
    """
    
    def __init__(self,
                 encoding_dim: int = 8,
                 threshold_percentile: float = 95.0,
                 model_manager: Optional[ModelPersistenceManager] = None):
        """
        Initialize AutoEncoder detector.
        
        Args:
            encoding_dim: Size of the encoding layer
            threshold_percentile: Percentile for anomaly threshold
            model_manager: Optional custom model manager
        """
        self.encoding_dim = encoding_dim
        self.threshold_percentile = threshold_percentile
        self.model_manager = model_manager or globals()['model_manager']
        
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        self._is_fitted = False
    
    def _build_model(self, input_dim: int) -> tf.keras.Model:
        """Build autoencoder architecture"""
        from tensorflow.keras.layers import Input
        from tensorflow.keras.models import Model
        
        input_layer = Input(shape=(input_dim,))
        
        # Encoder
        encoded = Dense(32, activation='relu')(input_layer)
        encoded = Dropout(0.2)(encoded)
        encoded = Dense(16, activation='relu')(encoded)
        encoded = Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = Dense(16, activation='relu')(encoded)
        decoded = Dropout(0.2)(decoded)
        decoded = Dense(32, activation='relu')(decoded)
        decoded = Dense(input_dim, activation='linear')(decoded)
        
        model = Model(input_layer, decoded)
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare multivariate features"""
        features = data[['close', 'volume']].copy()
        features['returns'] = data['close'].pct_change()
        features['volume_change'] = data['volume'].pct_change()
        features['high_low_ratio'] = data['high'] / (data['low'] + 1e-10)
        features['close_open_ratio'] = data['close'] / (data['open'] + 1e-10)
        features = features.dropna()
        
        return self.scaler.fit_transform(features)
    
    def fit(self, data: pd.DataFrame, symbol: str = 'UNKNOWN',
            epochs: int = 100, batch_size: int = 32) -> 'AutoEncoderAnomalyDetector':
        """Train the autoencoder"""
        features = self.prepare_features(data)
        
        # Build and train
        self.model = self._build_model(features.shape[1])
        
        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='loss', patience=10, restore_best_weights=True
        )
        
        self.model.fit(
            features, features,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
            callbacks=[early_stop]
        )
        
        # Calculate threshold from training data
        reconstructions = self.model.predict(features, verbose=0)
        mse = np.mean(np.power(features - reconstructions, 2), axis=1)
        self.threshold = np.percentile(mse, self.threshold_percentile)
        
        self._is_fitted = True
        logger.info(f"AutoEncoder trained for {symbol}, threshold: {self.threshold:.6f}")
        
        return self
    
    def detect_anomalies(self, data: pd.DataFrame,
                        symbol: str = 'UNKNOWN') -> List[AnomalyResult]:
        """Detect anomalies using reconstruction error"""
        if not self._is_fitted:
            self.fit(data, symbol)
        
        features = self.prepare_features(data)
        reconstructions = self.model.predict(features, verbose=0)
        
        mse = np.mean(np.power(features - reconstructions, 2), axis=1)
        
        anomalies = []
        offset = len(data) - len(mse)  # Account for dropped NaN rows
        
        for i, error in enumerate(mse):
            if error > self.threshold:
                data_idx = i + offset
                anomalies.append(AnomalyResult(
                    date=data['date'].iloc[data_idx],
                    score=float(error / self.threshold),
                    threshold=1.0,
                    is_anomaly=True,
                    method='autoencoder',
                    details={
                        'price': float(data['close'].iloc[data_idx]),
                        'volume': int(data['volume'].iloc[data_idx]),
                        'reconstruction_error': float(error),
                        'threshold': float(self.threshold)
                    }
                ))
        
        logger.info(f"AutoEncoder detected {len(anomalies)} anomalies for {symbol}")
        return anomalies