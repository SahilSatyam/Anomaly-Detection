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
        
        anomalies = []
        for i in range(len(data)):
            if i < self.window_size:
                continue
                
            price = data['close'].iloc[i]
            date = data['date'].iloc[i]
            
            # Calculate percentage deviation from bands
            upper_deviation = (price - upper_band.iloc[i]) / upper_band.iloc[i] * 100
            lower_deviation = (price - lower_band.iloc[i]) / lower_band.iloc[i] * 100
            
            # Determine if price is outside bands
            is_anomaly = price > upper_band.iloc[i] or price < lower_band.iloc[i]
            
            if is_anomaly:
                score = max(abs(upper_deviation), abs(lower_deviation))
                anomalies.append(AnomalyResult(
                    date=date,
                    score=score,
                    threshold=self.num_std,
                    is_anomaly=True,
                    method='bollinger_bands',
                    details={
                        'price': price,
                        'middle_band': middle_band.iloc[i],
                        'upper_band': upper_band.iloc[i],
                        'lower_band': lower_band.iloc[i],
                        'upper_deviation': upper_deviation,
                        'lower_deviation': lower_deviation
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
        
        anomalies = []
        for i in range(len(data)):
            if i < self.window_size:
                continue
                
            z_score = z_scores.iloc[i]
            date = data['date'].iloc[i]
            
            # Check if absolute Z-score exceeds threshold
            is_anomaly = abs(z_score) > self.num_std
            
            if is_anomaly:
                anomalies.append(AnomalyResult(
                    date=date,
                    score=abs(z_score),
                    threshold=self.num_std,
                    is_anomaly=True,
                    method='zscore',
                    details={
                        'price': data['close'].iloc[i],
                        'z_score': z_score,
                        'rolling_mean': data['close'].rolling(window=self.window_size).mean().iloc[i],
                        'rolling_std': data['close'].rolling(window=self.window_size).std().iloc[i]
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
        volume_mean = data['volume'].rolling(window=self.window_size).mean()
        volume_std = data['volume'].rolling(window=self.window_size).std()
        volume_z_scores = (data['volume'] - volume_mean) / volume_std
        
        anomalies = []
        for i in range(len(data)):
            if i < self.window_size:
                continue
                
            z_score = volume_z_scores.iloc[i]
            date = data['date'].iloc[i]
            
            # Check if absolute Z-score exceeds threshold
            is_anomaly = abs(z_score) > self.num_std
            
            if is_anomaly:
                anomalies.append(AnomalyResult(
                    date=date,
                    score=abs(z_score),
                    threshold=self.num_std,
                    is_anomaly=True,
                    method='volume_zscore',
                    details={
                        'volume': data['volume'].iloc[i],
                        'z_score': z_score,
                        'rolling_mean': volume_mean.iloc[i],
                        'rolling_std': volume_std.iloc[i]
                    }
                ))
                
        return anomalies 