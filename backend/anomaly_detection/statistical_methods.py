import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AnomalyResult:
    date: Any
    score: float
    threshold: float
    is_anomaly: bool
    method: str
    details: Dict
    # New fields for test compatibility (added with defaults to preserve positional arg order)
    price: Optional[float] = None
    volume: Optional[int] = None
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert AnomalyResult to dictionary."""
        result = asdict(self)
        if isinstance(self.date, (datetime, pd.Timestamp)):
            result['date'] = self.date.isoformat()
        return result

class StatisticalAnomalyDetector:
    def __init__(self, window_size: int = 20, num_std: float = 2.0, **kwargs):
        """
        Initialize the statistical anomaly detector
        
        Args:
            window_size (int): Size of the rolling window for calculations
            num_std (float): Number of standard deviations for threshold
        """
        # Original attributes
        self.window_size = window_size
        self.num_std = num_std

        # Attribute names expected by tests
        self.bollinger_window = kwargs.get('bollinger_window', window_size)
        self.bollinger_std = kwargs.get('bollinger_std', num_std)
        self.zscore_threshold = kwargs.get('zscore_threshold', num_std)

    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands for price data
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: Middle band, upper band, lower band
        """
        middle_band = data['close'].rolling(window=self.bollinger_window).mean()
        std = data['close'].rolling(window=self.bollinger_window).std()
        
        upper_band = middle_band + (std * self.bollinger_std)
        lower_band = middle_band - (std * self.bollinger_std)
        
        return middle_band, upper_band, lower_band

    def _get_severity(self, score: float, threshold: float) -> str:
        """Determine severity based on how much the score exceeds the threshold."""
        ratio = abs(score) / (threshold if threshold != 0 else 1.0)
        if ratio > 2.0:
            return 'high'
        elif ratio > 1.5:
            return 'medium'
        else:
            return 'low'

    def detect_bollinger_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using Bollinger Bands
        
        Args:
            data (pd.DataFrame): DataFrame with 'close' prices and 'date'
            
        Returns:
            List[AnomalyResult]: List of detected anomalies
        """
        if data.empty or len(data) < self.bollinger_window:
            return []

        middle_band, upper_band, lower_band = self.calculate_bollinger_bands(data)
        
        prices = data['close']
        is_upper = prices > upper_band
        is_lower = prices < lower_band
        is_anomaly_mask = (is_upper | is_lower).values

        # Apply window constraint
        is_anomaly_mask[:self.bollinger_window] = False

        anomaly_positions = np.where(is_anomaly_mask)[0]

        upper_deviations = ((prices - upper_band) / upper_band * 100)
        lower_deviations = ((prices - lower_band) / lower_band * 100)

        anomalies = []
        for i in anomaly_positions:
            price = float(prices.iloc[i])
            date = data['date'].iloc[i]
            
            u_dev = float(upper_deviations.iloc[i])
            l_dev = float(lower_deviations.iloc[i])
            
            score = max(abs(u_dev), abs(l_dev))
            anomaly_type = 'price_high' if is_upper.iloc[i] else 'price_low'
            
            anomalies.append(AnomalyResult(
                date=date,
                score=score,
                threshold=self.bollinger_std,
                is_anomaly=True,
                method='bollinger_bands',
                price=price,
                anomaly_type=anomaly_type,
                severity=self._get_severity(score, 5.0), # Using 5% as a base for deviation severity
                details={
                    'price': price,
                    'middle_band': float(middle_band.iloc[i]),
                    'upper_band': float(upper_band.iloc[i]),
                    'lower_band': float(lower_band.iloc[i]),
                    'upper_deviation': u_dev,
                    'lower_deviation': l_dev
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
        rolling_mean = data['close'].rolling(window=self.bollinger_window).mean()
        rolling_std = data['close'].rolling(window=self.bollinger_window).std()
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
        if data.empty or len(data) < self.bollinger_window:
            return []

        z_scores = self.calculate_zscore(data)
        # To avoid redundant calculation in details, we'll use rolling mean/std
        # but for performance optimization we only loop over anomalies
        rolling_mean = data['close'].rolling(window=self.bollinger_window).mean()
        rolling_std = data['close'].rolling(window=self.bollinger_window).std()

        is_anomaly_mask = (z_scores.abs() > self.zscore_threshold).values
        is_anomaly_mask[:self.bollinger_window] = False

        anomaly_positions = np.where(is_anomaly_mask)[0]
        
        anomalies = []
        for i in anomaly_positions:
            z_score = float(z_scores.iloc[i])
            price = float(data['close'].iloc[i])
            
            anomalies.append(AnomalyResult(
                date=data['date'].iloc[i],
                score=abs(z_score),
                threshold=self.zscore_threshold,
                is_anomaly=True,
                method='zscore',
                price=price,
                anomaly_type='price',
                severity=self._get_severity(z_score, self.zscore_threshold),
                details={
                    'price': price,
                    'z_score': z_score,
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
        if data.empty or len(data) < self.bollinger_window:
            return []

        volume_mean = data['volume'].rolling(window=self.bollinger_window).mean()
        volume_std = data['volume'].rolling(window=self.bollinger_window).std()
        volume_z_scores = (data['volume'] - volume_mean) / volume_std
        
        is_anomaly_mask = (volume_z_scores.abs() > self.zscore_threshold).values
        is_anomaly_mask[:self.bollinger_window] = False

        anomaly_positions = np.where(is_anomaly_mask)[0]

        anomalies = []
        for i in anomaly_positions:
            z_score = float(volume_z_scores.iloc[i])
            volume = int(data['volume'].iloc[i])
            
            anomalies.append(AnomalyResult(
                date=data['date'].iloc[i],
                score=abs(z_score),
                threshold=self.zscore_threshold,
                is_anomaly=True,
                method='volume_zscore',
                volume=volume,
                anomaly_type='volume',
                severity=self._get_severity(z_score, self.zscore_threshold),
                details={
                    'volume': volume,
                    'z_score': z_score,
                    'rolling_mean': float(volume_mean.iloc[i]),
                    'rolling_std': float(volume_std.iloc[i])
                }
            ))
                
        return anomalies
