"""
Model Persistence Manager

Handles saving and loading of trained ML models to avoid retraining on every detection run.
Uses joblib for scikit-learn models and TensorFlow's native format for Keras models.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging
import joblib
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default model storage directory
DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')


class ModelMetadata:
    """Stores metadata about a trained model"""
    
    def __init__(self, 
                 model_type: str,
                 symbol: str,
                 trained_at: datetime,
                 data_hash: str,
                 hyperparameters: Dict[str, Any],
                 metrics: Optional[Dict[str, float]] = None):
        self.model_type = model_type
        self.symbol = symbol
        self.trained_at = trained_at
        self.data_hash = data_hash
        self.hyperparameters = hyperparameters
        self.metrics = metrics or {}
    
    def to_dict(self) -> Dict:
        return {
            'model_type': self.model_type,
            'symbol': self.symbol,
            'trained_at': self.trained_at.isoformat(),
            'data_hash': self.data_hash,
            'hyperparameters': self.hyperparameters,
            'metrics': self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelMetadata':
        return cls(
            model_type=data['model_type'],
            symbol=data['symbol'],
            trained_at=datetime.fromisoformat(data['trained_at']),
            data_hash=data['data_hash'],
            hyperparameters=data['hyperparameters'],
            metrics=data.get('metrics', {})
        )
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if model is older than max_age_hours"""
        age = datetime.utcnow() - self.trained_at
        return age > timedelta(hours=max_age_hours)


class ModelPersistenceManager:
    """
    Manages saving and loading of trained ML models.
    
    Features:
    - Save scikit-learn models with joblib
    - Save Keras/TensorFlow models in native format
    - Track model metadata (training date, data hash, hyperparameters)
    - Automatic model invalidation based on age and data changes
    - Model versioning per stock symbol
    """
    
    def __init__(self, model_dir: str = None):
        """
        Initialize the model persistence manager.
        
        Args:
            model_dir: Directory to store models. Defaults to ./models
        """
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self._ensure_model_dir()
    
    def _ensure_model_dir(self):
        """Create model directory if it doesn't exist"""
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Model directory: {self.model_dir}")
    
    def _get_model_path(self, model_type: str, symbol: str, extension: str = '.joblib') -> str:
        """Get the file path for a model"""
        filename = f"{model_type}_{symbol.upper()}{extension}"
        return os.path.join(self.model_dir, filename)
    
    def _get_metadata_path(self, model_type: str, symbol: str) -> str:
        """Get the file path for model metadata"""
        return self._get_model_path(model_type, symbol, '_metadata.json')
    
    @staticmethod
    def compute_data_hash(data) -> str:
        """Compute a hash of the training data for change detection"""
        if hasattr(data, 'to_json'):
            # Pandas DataFrame
            data_str = data.to_json()
        elif isinstance(data, np.ndarray):
            data_str = data.tobytes()
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode() if isinstance(data_str, str) else data_str).hexdigest()[:16]
    
    def save_sklearn_model(self, 
                          model, 
                          model_type: str,
                          symbol: str,
                          data_hash: str,
                          hyperparameters: Dict[str, Any],
                          scaler=None,
                          metrics: Optional[Dict[str, float]] = None) -> str:
        """
        Save a scikit-learn model and its associated scaler.
        
        Args:
            model: The trained scikit-learn model
            model_type: Type of model (e.g., 'isolation_forest')
            symbol: Stock symbol the model was trained on
            data_hash: Hash of training data
            hyperparameters: Model hyperparameters
            scaler: Optional StandardScaler or similar
            metrics: Optional training metrics
            
        Returns:
            Path to saved model
        """
        model_path = self._get_model_path(model_type, symbol, '.joblib')
        metadata_path = self._get_metadata_path(model_type, symbol)
        
        # Save model and scaler together
        model_data = {
            'model': model,
            'scaler': scaler
        }
        joblib.dump(model_data, model_path)
        
        # Save metadata
        metadata = ModelMetadata(
            model_type=model_type,
            symbol=symbol,
            trained_at=datetime.utcnow(),
            data_hash=data_hash,
            hyperparameters=hyperparameters,
            metrics=metrics
        )
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        logger.info(f"Saved {model_type} model for {symbol} to {model_path}")
        return model_path
    
    def load_sklearn_model(self, 
                          model_type: str, 
                          symbol: str,
                          data_hash: Optional[str] = None,
                          max_age_hours: int = 24) -> Tuple[Any, Any, Optional[ModelMetadata]]:
        """
        Load a scikit-learn model if it exists and is valid.
        
        Args:
            model_type: Type of model
            symbol: Stock symbol
            data_hash: Optional hash to validate against
            max_age_hours: Maximum model age in hours
            
        Returns:
            Tuple of (model, scaler, metadata) or (None, None, None) if not found/invalid
        """
        model_path = self._get_model_path(model_type, symbol, '.joblib')
        metadata_path = self._get_metadata_path(model_type, symbol)
        
        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            logger.info(f"No cached {model_type} model found for {symbol}")
            return None, None, None
        
        # Load and validate metadata
        try:
            with open(metadata_path, 'r') as f:
                metadata = ModelMetadata.from_dict(json.load(f))
        except Exception as e:
            logger.warning(f"Error loading model metadata: {e}")
            return None, None, None
        
        # Check if model is expired
        if metadata.is_expired(max_age_hours):
            logger.info(f"Cached {model_type} model for {symbol} is expired")
            return None, None, None
        
        # Check if data has changed
        if data_hash and metadata.data_hash != data_hash:
            logger.info(f"Training data has changed for {symbol}, model needs retraining")
            return None, None, None
        
        # Load model
        try:
            model_data = joblib.load(model_path)
            logger.info(f"Loaded cached {model_type} model for {symbol} (trained {metadata.trained_at})")
            return model_data['model'], model_data.get('scaler'), metadata
        except Exception as e:
            logger.warning(f"Error loading model: {e}")
            return None, None, None
    
    def save_keras_model(self,
                        model,
                        model_type: str,
                        symbol: str,
                        data_hash: str,
                        hyperparameters: Dict[str, Any],
                        scaler=None,
                        metrics: Optional[Dict[str, float]] = None) -> str:
        """
        Save a Keras/TensorFlow model.
        
        Args:
            model: The trained Keras model
            model_type: Type of model (e.g., 'lstm')
            symbol: Stock symbol
            data_hash: Hash of training data
            hyperparameters: Model hyperparameters
            scaler: Optional scaler
            metrics: Optional training metrics
            
        Returns:
            Path to saved model directory
        """
        # Keras models are saved as directories
        model_path = self._get_model_path(model_type, symbol, '_keras')
        scaler_path = self._get_model_path(model_type, symbol, '_scaler.joblib')
        metadata_path = self._get_metadata_path(model_type, symbol)
        
        # Save Keras model
        model.save(model_path)
        
        # Save scaler separately
        if scaler is not None:
            joblib.dump(scaler, scaler_path)
        
        # Save metadata
        metadata = ModelMetadata(
            model_type=model_type,
            symbol=symbol,
            trained_at=datetime.utcnow(),
            data_hash=data_hash,
            hyperparameters=hyperparameters,
            metrics=metrics
        )
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        logger.info(f"Saved {model_type} Keras model for {symbol} to {model_path}")
        return model_path
    
    def load_keras_model(self,
                        model_type: str,
                        symbol: str,
                        data_hash: Optional[str] = None,
                        max_age_hours: int = 24) -> Tuple[Any, Any, Optional[ModelMetadata]]:
        """
        Load a Keras model if it exists and is valid.
        
        Args:
            model_type: Type of model
            symbol: Stock symbol
            data_hash: Optional hash to validate against
            max_age_hours: Maximum model age in hours
            
        Returns:
            Tuple of (model, scaler, metadata) or (None, None, None) if not found/invalid
        """
        from tensorflow import keras
        
        model_path = self._get_model_path(model_type, symbol, '_keras')
        scaler_path = self._get_model_path(model_type, symbol, '_scaler.joblib')
        metadata_path = self._get_metadata_path(model_type, symbol)
        
        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            logger.info(f"No cached {model_type} Keras model found for {symbol}")
            return None, None, None
        
        # Load and validate metadata
        try:
            with open(metadata_path, 'r') as f:
                metadata = ModelMetadata.from_dict(json.load(f))
        except Exception as e:
            logger.warning(f"Error loading model metadata: {e}")
            return None, None, None
        
        # Check if model is expired
        if metadata.is_expired(max_age_hours):
            logger.info(f"Cached {model_type} Keras model for {symbol} is expired")
            return None, None, None
        
        # Check if data has changed
        if data_hash and metadata.data_hash != data_hash:
            logger.info(f"Training data has changed for {symbol}, model needs retraining")
            return None, None, None
        
        # Load model and scaler
        try:
            model = keras.models.load_model(model_path)
            scaler = None
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
            
            logger.info(f"Loaded cached {model_type} Keras model for {symbol}")
            return model, scaler, metadata
        except Exception as e:
            logger.warning(f"Error loading Keras model: {e}")
            return None, None, None
    
    def delete_model(self, model_type: str, symbol: str) -> bool:
        """Delete a saved model and its metadata"""
        import shutil
        
        deleted = False
        
        # Try different extensions
        for ext in ['.joblib', '_keras', '_scaler.joblib', '_metadata.json']:
            path = self._get_model_path(model_type, symbol, ext)
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted = True
        
        if deleted:
            logger.info(f"Deleted {model_type} model for {symbol}")
        
        return deleted
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all saved models with their metadata"""
        models = {}
        
        for filename in os.listdir(self.model_dir):
            if filename.endswith('_metadata.json'):
                try:
                    with open(os.path.join(self.model_dir, filename), 'r') as f:
                        metadata = ModelMetadata.from_dict(json.load(f))
                    key = f"{metadata.model_type}_{metadata.symbol}"
                    models[key] = {
                        **metadata.to_dict(),
                        'is_expired': metadata.is_expired()
                    }
                except Exception as e:
                    logger.warning(f"Error reading metadata from {filename}: {e}")
        
        return models
    
    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Delete all expired models"""
        deleted_count = 0
        
        for filename in os.listdir(self.model_dir):
            if filename.endswith('_metadata.json'):
                try:
                    with open(os.path.join(self.model_dir, filename), 'r') as f:
                        metadata = ModelMetadata.from_dict(json.load(f))
                    
                    if metadata.is_expired(max_age_hours):
                        if self.delete_model(metadata.model_type, metadata.symbol):
                            deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error checking {filename}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} expired models")
        return deleted_count


# Global instance for convenience
model_manager = ModelPersistenceManager()
