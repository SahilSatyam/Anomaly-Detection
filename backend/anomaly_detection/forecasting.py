"""
Time-Series Forecasting Methods

Implements ARIMA and Prophet-based forecasting for stock price prediction
and anomaly detection based on forecast deviations.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import warnings

from .statistical_methods import AnomalyResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress statsmodels warnings
warnings.filterwarnings('ignore', category=UserWarning)


class ARIMAForecaster:
    """
    ARIMA-based time series forecasting and anomaly detection.
    
    Uses Auto-ARIMA (pmdarima) to automatically find optimal parameters.
    Anomalies are detected when actual values deviate significantly from forecasts.
    """
    
    def __init__(self, 
                 seasonal: bool = True,
                 m: int = 5,  # Weekly seasonality for stock data (5 trading days)
                 threshold_std: float = 2.0):
        """
        Initialize ARIMA forecaster.
        
        Args:
            seasonal: Whether to use seasonal ARIMA (SARIMA)
            m: Season period (5 for weekly in trading days)
            threshold_std: Number of std deviations for anomaly detection
        """
        self.seasonal = seasonal
        self.m = m
        self.threshold_std = threshold_std
        self.model = None
        self.fitted = False
    
    def fit(self, data: pd.DataFrame, target_col: str = 'close') -> 'ARIMAForecaster':
        """
        Fit ARIMA model to the data.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to forecast
            
        Returns:
            self for method chaining
        """
        try:
            from pmdarima import auto_arima
            
            # Prepare data
            y = data[target_col].values
            
            # Fit auto-ARIMA
            logger.info("Fitting Auto-ARIMA model...")
            self.model = auto_arima(
                y,
                seasonal=self.seasonal,
                m=self.m if self.seasonal else 1,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore',
                max_p=5, max_q=5,
                max_P=2, max_Q=2,
                max_order=10,
                trace=False
            )
            
            self.fitted = True
            logger.info(f"ARIMA model fitted: {self.model.order}, seasonal: {self.model.seasonal_order}")
            return self
            
        except ImportError:
            logger.error("pmdarima not installed. Install with: pip install pmdarima")
            raise
        except Exception as e:
            logger.error(f"Error fitting ARIMA model: {e}")
            raise
    
    def forecast(self, steps: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate forecast with confidence intervals.
        
        Args:
            steps: Number of steps to forecast
            
        Returns:
            Tuple of (forecasts, confidence_intervals)
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        forecast, conf_int = self.model.predict(n_periods=steps, return_conf_int=True)
        return forecast, conf_int
    
    def detect_anomalies(self, data: pd.DataFrame, 
                        target_col: str = 'close') -> List[AnomalyResult]:
        """
        Detect anomalies using ARIMA forecast residuals.
        
        Uses a rolling window approach: fits model on historical data,
        forecasts next point, compares with actual.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to analyze
            
        Returns:
            List of detected anomalies
        """
        try:
            from pmdarima import auto_arima
            
            anomalies = []
            y = data[target_col].values
            dates = data['date'].values
            
            # Minimum training window
            min_window = 30
            
            if len(y) < min_window + 1:
                logger.warning(f"Insufficient data for ARIMA anomaly detection (need {min_window + 1}+)")
                return anomalies
            
            residuals = []
            
            # Rolling window forecast
            for i in range(min_window, len(y)):
                try:
                    # Fit on historical data
                    train_data = y[:i]
                    
                    # Quick ARIMA fit (less thorough for speed)
                    model = auto_arima(
                        train_data,
                        seasonal=False,  # Disable seasonal for speed
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        max_p=3, max_q=3,
                        max_order=5,
                        trace=False
                    )
                    
                    # One-step forecast
                    forecast = model.predict(n_periods=1)[0]
                    actual = y[i]
                    
                    # Calculate residual
                    residual = actual - forecast
                    residuals.append(residual)
                    
                except Exception:
                    continue
            
            if not residuals:
                return anomalies
            
            # Calculate residual statistics
            residuals = np.array(residuals)
            mean_residual = np.mean(residuals)
            std_residual = np.std(residuals)
            
            # Detect anomalies
            for idx, residual in enumerate(residuals):
                data_idx = min_window + idx
                z_score = abs(residual - mean_residual) / (std_residual + 1e-10)
                
                if z_score > self.threshold_std:
                    anomalies.append(AnomalyResult(
                        date=dates[data_idx],
                        score=z_score,
                        threshold=self.threshold_std,
                        is_anomaly=True,
                        method='arima',
                        details={
                            'price': float(y[data_idx]),
                            'forecast': float(y[data_idx] - residual),
                            'residual': float(residual),
                            'mean_residual': float(mean_residual),
                            'std_residual': float(std_residual)
                        }
                    ))
            
            logger.info(f"ARIMA detected {len(anomalies)} anomalies")
            return anomalies
            
        except ImportError:
            logger.error("pmdarima not installed for ARIMA analysis")
            return []
        except Exception as e:
            logger.error(f"Error in ARIMA anomaly detection: {e}")
            return []


class ProphetForecaster:
    """
    Prophet-based time series forecasting and anomaly detection.
    
    Facebook Prophet is particularly good at handling:
    - Missing data
    - Holidays and special events
    - Multiple seasonalities
    - Trend changes
    """
    
    def __init__(self,
                 yearly_seasonality: bool = True,
                 weekly_seasonality: bool = True,
                 daily_seasonality: bool = False,
                 changepoint_prior_scale: float = 0.05,
                 threshold_std: float = 2.0):
        """
        Initialize Prophet forecaster.
        
        Args:
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality
            changepoint_prior_scale: Flexibility of trend changes
            threshold_std: Number of std deviations for anomaly detection
        """
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.changepoint_prior_scale = changepoint_prior_scale
        self.threshold_std = threshold_std
        self.model = None
        self.fitted = False
    
    def _prepare_data(self, data: pd.DataFrame, target_col: str = 'close') -> pd.DataFrame:
        """Prepare data in Prophet format (ds, y columns)"""
        df = pd.DataFrame()
        
        # Handle date column
        if 'date' in data.columns:
            df['ds'] = pd.to_datetime(data['date'])
        elif data.index.name == 'date' or isinstance(data.index, pd.DatetimeIndex):
            df['ds'] = pd.to_datetime(data.index)
        else:
            raise ValueError("Data must have a 'date' column or DatetimeIndex")
        
        df['y'] = data[target_col].values
        
        # Remove timezone if present
        if df['ds'].dt.tz is not None:
            df['ds'] = df['ds'].dt.tz_localize(None)
        
        return df
    
    def fit(self, data: pd.DataFrame, target_col: str = 'close') -> 'ProphetForecaster':
        """
        Fit Prophet model to the data.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to forecast
            
        Returns:
            self for method chaining
        """
        try:
            from prophet import Prophet
            
            # Prepare data
            df = self._prepare_data(data, target_col)
            
            # Initialize and fit model
            logger.info("Fitting Prophet model...")
            self.model = Prophet(
                yearly_seasonality=self.yearly_seasonality,
                weekly_seasonality=self.weekly_seasonality,
                daily_seasonality=self.daily_seasonality,
                changepoint_prior_scale=self.changepoint_prior_scale
            )
            
            # Suppress Prophet's verbose output
            self.model.fit(df)
            
            self.fitted = True
            logger.info("Prophet model fitted successfully")
            return self
            
        except ImportError:
            logger.error("Prophet not installed. Install with: pip install prophet")
            raise
        except Exception as e:
            logger.error(f"Error fitting Prophet model: {e}")
            raise
    
    def forecast(self, periods: int = 30, 
                freq: str = 'D') -> pd.DataFrame:
        """
        Generate forecast with uncertainty intervals.
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'B' for business days)
            
        Returns:
            DataFrame with forecast results
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']]
    
    def detect_anomalies(self, data: pd.DataFrame,
                        target_col: str = 'close') -> List[AnomalyResult]:
        """
        Detect anomalies based on Prophet forecast intervals.
        
        Points outside the uncertainty interval are flagged as anomalies.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to analyze
            
        Returns:
            List of detected anomalies
        """
        try:
            from prophet import Prophet
            
            # Fit model if not already fitted
            if not self.fitted:
                self.fit(data, target_col)
            
            # Prepare data and generate in-sample predictions
            df = self._prepare_data(data, target_col)
            forecast = self.model.predict(df)
            
            # Merge actual values with forecast
            forecast['y_actual'] = df['y'].values
            
            # Detect anomalies (outside prediction interval)
            anomalies = []
            
            for _, row in forecast.iterrows():
                actual = row['y_actual']
                predicted = row['yhat']
                lower = row['yhat_lower']
                upper = row['yhat_upper']
                
                # Calculate deviation score
                if actual > upper:
                    deviation = (actual - upper) / (upper - predicted + 1e-10)
                    is_anomaly = True
                elif actual < lower:
                    deviation = (lower - actual) / (predicted - lower + 1e-10)
                    is_anomaly = True
                else:
                    deviation = 0
                    is_anomaly = False
                
                # Apply threshold
                if is_anomaly and deviation > self.threshold_std:
                    anomalies.append(AnomalyResult(
                        date=row['ds'],
                        score=deviation,
                        threshold=self.threshold_std,
                        is_anomaly=True,
                        method='prophet',
                        details={
                            'price': float(actual),
                            'predicted': float(predicted),
                            'lower_bound': float(lower),
                            'upper_bound': float(upper),
                            'trend': float(row['trend']),
                            'deviation': float(deviation)
                        }
                    ))
            
            logger.info(f"Prophet detected {len(anomalies)} anomalies")
            return anomalies
            
        except ImportError:
            logger.error("Prophet not installed for analysis")
            return []
        except Exception as e:
            logger.error(f"Error in Prophet anomaly detection: {e}")
            return []


class TrendAnalyzer:
    """
    Combines multiple time-series methods for comprehensive trend analysis.
    """
    
    def __init__(self,
                 use_arima: bool = True,
                 use_prophet: bool = True,
                 threshold_std: float = 2.0):
        """
        Initialize trend analyzer.
        
        Args:
            use_arima: Enable ARIMA analysis
            use_prophet: Enable Prophet analysis
            threshold_std: Anomaly detection threshold
        """
        self.use_arima = use_arima
        self.use_prophet = use_prophet
        self.threshold_std = threshold_std
        
        self.arima = ARIMAForecaster(threshold_std=threshold_std) if use_arima else None
        self.prophet = ProphetForecaster(threshold_std=threshold_std) if use_prophet else None
    
    def analyze(self, data: pd.DataFrame, 
               target_col: str = 'close') -> Dict[str, List[AnomalyResult]]:
        """
        Run all enabled time-series analyses.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to analyze
            
        Returns:
            Dictionary of anomalies by method
        """
        results = {}
        
        if self.use_arima and self.arima:
            try:
                results['arima'] = self.arima.detect_anomalies(data, target_col)
            except Exception as e:
                logger.warning(f"ARIMA analysis failed: {e}")
                results['arima'] = []
        
        if self.use_prophet and self.prophet:
            try:
                results['prophet'] = self.prophet.detect_anomalies(data, target_col)
            except Exception as e:
                logger.warning(f"Prophet analysis failed: {e}")
                results['prophet'] = []
        
        return results
    
    def get_consensus_anomalies(self, data: pd.DataFrame,
                               target_col: str = 'close',
                               min_methods: int = 1) -> List[AnomalyResult]:
        """
        Get anomalies detected by multiple methods.
        
        Args:
            data: DataFrame with time series data
            target_col: Column to analyze
            min_methods: Minimum methods that must agree
            
        Returns:
            List of consensus anomalies
        """
        all_results = self.analyze(data, target_col)
        
        # Group by date
        by_date = {}
        for method, anomalies in all_results.items():
            for anomaly in anomalies:
                date_key = str(anomaly.date)
                if date_key not in by_date:
                    by_date[date_key] = {'methods': set(), 'anomalies': []}
                by_date[date_key]['methods'].add(method)
                by_date[date_key]['anomalies'].append(anomaly)
        
        # Filter by consensus
        consensus = []
        for date_key, info in by_date.items():
            if len(info['methods']) >= min_methods:
                best = max(info['anomalies'], key=lambda x: x.score)
                best.details['detecting_methods'] = list(info['methods'])
                consensus.append(best)
        
        return sorted(consensus, key=lambda x: str(x.date))
