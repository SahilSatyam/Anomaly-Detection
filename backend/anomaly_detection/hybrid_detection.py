from typing import List, Dict
import pandas as pd
from .statistical_methods import StatisticalAnomalyDetector, AnomalyResult
from .ml_models import MLAnomalyDetector, LSTMAnomalyDetector

class HybridAnomalyDetector:
    def __init__(self, 
                 window_size: int = 20,
                 num_std: float = 2.0,
                 contamination: float = 0.1,
                 sequence_length: int = 10,
                 lstm_threshold: float = 2.0):
        """
        Initialize the hybrid anomaly detector
        
        Args:
            window_size (int): Size of the rolling window for statistical methods
            num_std (float): Number of standard deviations for statistical methods
            contamination (float): Expected proportion of anomalies for Isolation Forest
            sequence_length (int): Number of time steps for LSTM
            lstm_threshold (float): Threshold for LSTM anomaly detection
        """
        self.statistical_detector = StatisticalAnomalyDetector(
            window_size=window_size,
            num_std=num_std
        )
        
        self.ml_detector = MLAnomalyDetector(
            contamination=contamination
        )
        
        self.lstm_detector = LSTMAnomalyDetector(
            sequence_length=sequence_length,
            threshold=lstm_threshold
        )
        
    def detect_anomalies(self, data: pd.DataFrame) -> Dict[str, List[AnomalyResult]]:
        """
        Detect anomalies using all methods
        
        Args:
            data (pd.DataFrame): DataFrame with price and volume data
            
        Returns:
            Dict[str, List[AnomalyResult]]: Dictionary of anomalies detected by each method
        """
        # Detect anomalies using statistical methods
        bollinger_anomalies = self.statistical_detector.detect_bollinger_anomalies(data)
        zscore_anomalies = self.statistical_detector.detect_zscore_anomalies(data)
        volume_anomalies = self.statistical_detector.detect_volume_anomalies(data)
        
        # Detect anomalies using Isolation Forest
        isolation_forest_anomalies = self.ml_detector.detect_isolation_forest_anomalies(data)
        
        # Train LSTM model and detect anomalies
        self.lstm_detector.train(data)
        lstm_anomalies = self.lstm_detector.detect_lstm_anomalies(data)
        
        return {
            'bollinger_bands': bollinger_anomalies,
            'zscore': zscore_anomalies,
            'volume': volume_anomalies,
            'isolation_forest': isolation_forest_anomalies,
            'lstm': lstm_anomalies
        }
        
    def get_consensus_anomalies(self, data: pd.DataFrame, 
                              min_methods: int = 2) -> List[AnomalyResult]:
        """
        Get anomalies detected by multiple methods
        
        Args:
            data (pd.DataFrame): DataFrame with price and volume data
            min_methods (int): Minimum number of methods that must detect an anomaly
            
        Returns:
            List[AnomalyResult]: List of consensus anomalies
        """
        all_anomalies = self.detect_anomalies(data)
        
        # Create a dictionary to count anomalies by date
        anomaly_counts = {}
        
        # Count anomalies by date for each method
        for method, anomalies in all_anomalies.items():
            for anomaly in anomalies:
                date = anomaly.date
                if date not in anomaly_counts:
                    anomaly_counts[date] = {
                        'count': 0,
                        'methods': set(),
                        'anomalies': []
                    }
                anomaly_counts[date]['count'] += 1
                anomaly_counts[date]['methods'].add(method)
                anomaly_counts[date]['anomalies'].append(anomaly)
        
        # Filter for dates with enough method agreement
        consensus_anomalies = []
        for date, info in anomaly_counts.items():
            if info['count'] >= min_methods:
                # Use the anomaly with the highest score
                best_anomaly = max(info['anomalies'], 
                                 key=lambda x: x.score)
                
                # Add method information to details
                best_anomaly.details['detecting_methods'] = list(info['methods'])
                best_anomaly.details['method_count'] = info['count']
                
                consensus_anomalies.append(best_anomaly)
        
        return sorted(consensus_anomalies, key=lambda x: x.date)
        
    def get_weighted_anomalies(self, data: pd.DataFrame,
                             method_weights: Dict[str, float] = None) -> List[AnomalyResult]:
        """
        Get weighted anomaly scores combining all methods
        
        Args:
            data (pd.DataFrame): DataFrame with price and volume data
            method_weights (Dict[str, float]): Weights for each method
            
        Returns:
            List[AnomalyResult]: List of weighted anomalies
        """
        if method_weights is None:
            method_weights = {
                'bollinger_bands': 0.2,
                'zscore': 0.2,
                'volume': 0.2,
                'isolation_forest': 0.2,
                'lstm': 0.2
            }
            
        all_anomalies = self.detect_anomalies(data)
        
        # Create a dictionary to store weighted scores by date
        weighted_scores = {}
        
        # Calculate weighted scores for each date
        for method, anomalies in all_anomalies.items():
            weight = method_weights.get(method, 0.0)
            for anomaly in anomalies:
                date = anomaly.date
                if date not in weighted_scores:
                    weighted_scores[date] = {
                        'score': 0.0,
                        'methods': set(),
                        'anomalies': []
                    }
                weighted_scores[date]['score'] += weight * anomaly.score
                weighted_scores[date]['methods'].add(method)
                weighted_scores[date]['anomalies'].append(anomaly)
        
        # Create weighted anomaly results
        weighted_anomalies = []
        for date, info in weighted_scores.items():
            if info['score'] > 0:  # Only include dates with positive weighted scores
                # Use the anomaly with the highest score as base
                base_anomaly = max(info['anomalies'], 
                                 key=lambda x: x.score)
                
                # Create new anomaly result with weighted score
                weighted_anomaly = AnomalyResult(
                    date=date,
                    score=info['score'],
                    threshold=1.0,  # Normalized threshold
                    is_anomaly=True,
                    method='hybrid_weighted',
                    details={
                        **base_anomaly.details,
                        'weighted_score': info['score'],
                        'detecting_methods': list(info['methods']),
                        'method_weights': method_weights
                    }
                )
                weighted_anomalies.append(weighted_anomaly)
        
        return sorted(weighted_anomalies, key=lambda x: x.date) 