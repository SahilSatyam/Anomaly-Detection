import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from typing import List, Tuple, Dict
from dataclasses import dataclass
from .statistical_methods import AnomalyResult

class MLAnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        """
        Initialize the ML-based anomaly detector
        
        Args:
            contamination (float): Expected proportion of anomalies in the data
        """
        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42
        )
        self.scaler = StandardScaler()
        
    def prepare_data(self, data: pd.DataFrame) -> np.ndarray:
        """
        Prepare data for ML models
        
        Args:
            data (pd.DataFrame): DataFrame with price and volume data
            
        Returns:
            np.ndarray: Scaled features
        """
        features = data[['close', 'volume']].copy()
        features['returns'] = data['close'].pct_change()
        features['volume_change'] = data['volume'].pct_change()
        features = features.dropna()
        
        return self.scaler.fit_transform(features)

    def detect_isolation_forest_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using Isolation Forest
        
        Args:
            data (pd.DataFrame): DataFrame with price and volume data
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        features = self.prepare_data(data)
        
        # Fit and predict
        self.isolation_forest.fit(features)
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
                        'price': data['close'].iloc[i],
                        'volume': data['volume'].iloc[i],
                        'returns': data['close'].pct_change().iloc[i],
                        'volume_change': data['volume'].pct_change().iloc[i],
                        'raw_score': scores[i-1]
                    }
                ))
                
        return anomalies

class LSTMAnomalyDetector:
    def __init__(self, sequence_length: int = 10, threshold: float = 2.0):
        """
        Initialize the LSTM-based anomaly detector
        
        Args:
            sequence_length (int): Number of time steps to use for prediction
            threshold (float): Threshold for anomaly detection
        """
        self.sequence_length = sequence_length
        self.threshold = threshold
        self.model = self._build_model()
        self.scaler = StandardScaler()
        
    def _build_model(self) -> Sequential:
        """
        Build LSTM model architecture
        
        Returns:
            Sequential: Compiled LSTM model
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
        Prepare sequences for LSTM model
        
        Args:
            data (pd.DataFrame): DataFrame with price data
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: X (sequences) and y (targets)
        """
        # Scale the data
        scaled_data = self.scaler.fit_transform(data[['close']].values)
        
        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length)])
            y.append(scaled_data[i + self.sequence_length])
            
        return np.array(X), np.array(y)
        
    def train(self, data: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> None:
        """
        Train the LSTM model
        
        Args:
            data (pd.DataFrame): Training data
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
        """
        X, y = self.prepare_sequences(data)
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
        
    def detect_lstm_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using LSTM predictions
        
        Args:
            data (pd.DataFrame): DataFrame with price data
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        X, y_true = self.prepare_sequences(data)
        y_pred = self.model.predict(X)
        
        # Calculate prediction errors
        errors = np.abs(y_true - y_pred)
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        
        anomalies = []
        for i in range(len(data) - self.sequence_length):
            if errors[i][0] > self.threshold * std_error:
                anomalies.append(AnomalyResult(
                    date=data['date'].iloc[i + self.sequence_length],
                    score=errors[i][0] / std_error,
                    threshold=self.threshold,
                    is_anomaly=True,
                    method='lstm',
                    details={
                        'price': data['close'].iloc[i + self.sequence_length],
                        'predicted_price': self.scaler.inverse_transform(y_pred[i])[0][0],
                        'error': errors[i][0],
                        'mean_error': mean_error,
                        'std_error': std_error
                    }
                ))
                
        return anomalies 