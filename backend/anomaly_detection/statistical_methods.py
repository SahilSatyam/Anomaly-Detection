import numpy as np
import pandas as pd
from typing import Tuple, List, Dict
from dataclasses import dataclass

@dataclass
class AnomalyResult:
    date: str
    score: float
    threshold: float
    is_anomaly: bool
    method: str
    details: Dict

class StatisticalAnomalyDetector:
    def __init__(self, window_size: int = 20, num_std: float = 2.0):
        """
        Initialize the statistical anomaly detector
        
        Args:
            window_size (int): Size of the rolling window for calculations
            num_std (float): Number of standard deviations for threshold
        """
        self.window_size = window_size
        self.num_std = num_std

    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands for price data
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: Middle band, upper band, lower band
        """
        middle_band = data['close'].rolling(window=self.window_size).mean()
        std = data['close'].rolling(window=self.window_size).std()
        
        upper_band = middle_band + (std * self.num_std)
        lower_band = middle_band - (std * self.num_std)
        
        return middle_band, upper_band, lower_band

    def detect_bollinger_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using Bollinger Bands
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices and 'date'
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        middle_band, upper_band, lower_band = self.calculate_bollinger_bands(data)
        
        # Calculate deviation for all points using vectorized operations
        prices = data['close']
        upper_deviations = (prices - upper_band) / upper_band * 100
        lower_deviations = (prices - lower_band) / lower_band * 100

        # Identify anomaly indices using vectorized operations
        is_anomaly_mask = (prices > upper_band) | (prices < lower_band)
        if len(data) > self.window_size:
            is_anomaly_mask.iloc[:self.window_size] = False

        anomaly_indices = np.where(is_anomaly_mask)[0]

        anomalies = []
        # Only iterate over the identified anomalies
        for i in anomaly_indices:
            upper_dev = upper_deviations.iloc[i]
            lower_dev = lower_deviations.iloc[i]
            
            anomalies.append(AnomalyResult(
                date=data['date'].iloc[i],
                score=float(max(abs(upper_dev), abs(lower_dev))),
                threshold=self.num_std,
                is_anomaly=True,
                method='bollinger_bands',
                details={
                    'price': float(prices.iloc[i]),
                    'middle_band': float(middle_band.iloc[i]),
                    'upper_band': float(upper_band.iloc[i]),
                    'lower_band': float(lower_band.iloc[i]),
                    'upper_deviation': float(upper_dev),
                    'lower_deviation': float(lower_dev)
                }
            ))
                
        return anomalies

    def calculate_zscore(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Z-scores for price data
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices
            
        Returns:
            pd.Series: Z-scores
        """
        rolling_mean = data['close'].rolling(window=self.window_size).mean()
        rolling_std = data['close'].rolling(window=self.window_size).std()
        z_scores = (data['close'] - rolling_mean) / rolling_std
        return z_scores

    def detect_zscore_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using Z-score method
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices and 'date'
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        z_scores = self.calculate_zscore(data)
        
        # Pre-calculate rolling statistics to avoid redundant calculations in the loop
        rolling_mean = data['close'].rolling(window=self.window_size).mean()
        rolling_std = data['close'].rolling(window=self.window_size).std()

        # Identify anomaly indices using vectorized operations
        # We start from window_size as in the original code
        is_anomaly_mask = (z_scores.abs() > self.num_std)
        if len(data) > self.window_size:
            is_anomaly_mask.iloc[:self.window_size] = False

        anomaly_indices = np.where(is_anomaly_mask)[0]

        anomalies = []
        # Only iterate over the identified anomalies
        for i in anomaly_indices:
            z_score = z_scores.iloc[i]
            anomalies.append(AnomalyResult(
                date=data['date'].iloc[i],
                score=float(abs(z_score)),
                threshold=self.num_std,
                is_anomaly=True,
                method='zscore',
                details={
                    'price': float(data['close'].iloc[i]),
                    'z_score': float(z_score),
                    'rolling_mean': float(rolling_mean.iloc[i]),
                    'rolling_std': float(rolling_std.iloc[i])
                }
            ))
                
        return anomalies

    def detect_volume_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect volume anomalies using Z-score method
        
        Args:
            data (pd.DataFrame): DataFrame with 'volume' and 'date'
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        volumes = data['volume']
        volume_mean = volumes.rolling(window=self.window_size).mean()
        volume_std = volumes.rolling(window=self.window_size).std()
        volume_z_scores = (volumes - volume_mean) / volume_std

        # Identify anomaly indices using vectorized operations
        is_anomaly_mask = (volume_z_scores.abs() > self.num_std)
        if len(data) > self.window_size:
            is_anomaly_mask.iloc[:self.window_size] = False

        anomaly_indices = np.where(is_anomaly_mask)[0]
        
        anomalies = []
        # Only iterate over the identified anomalies
        for i in anomaly_indices:
            z_score = volume_z_scores.iloc[i]
            anomalies.append(AnomalyResult(
                date=data['date'].iloc[i],
                score=float(abs(z_score)),
                threshold=self.num_std,
                is_anomaly=True,
                method='volume_zscore',
                details={
                    'volume': float(volumes.iloc[i]),
                    'z_score': float(z_score),
                    'rolling_mean': float(volume_mean.iloc[i]),
                    'rolling_std': float(volume_std.iloc[i])
                }
            ))
                
        return anomalies 