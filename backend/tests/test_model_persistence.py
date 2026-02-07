"""
Unit tests for Model Persistence Manager.

Tests cover:
- Model saving and loading
- Metadata management
- Cache invalidation
- Cleanup operations
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anomaly_detection.model_persistence import (
    ModelPersistenceManager,
    ModelMetadata
)


class TestModelMetadata:
    """Tests for ModelMetadata class."""
    
    def test_metadata_creation(self):
        """Test creating ModelMetadata instance."""
        metadata = ModelMetadata(
            model_type='isolation_forest',
            symbol='AAPL',
            trained_at=datetime.utcnow(),
            data_hash='abc123',
            hyperparameters={'contamination': 0.1},
            metrics={'precision': 0.85}
        )
        
        assert metadata.model_type == 'isolation_forest'
        assert metadata.symbol == 'AAPL'
        assert metadata.data_hash == 'abc123'
        assert metadata.hyperparameters['contamination'] == 0.1
        assert metadata.metrics['precision'] == 0.85
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        now = datetime.utcnow()
        metadata = ModelMetadata(
            model_type='lstm',
            symbol='GOOGL',
            trained_at=now,
            data_hash='def456',
            hyperparameters={'sequence_length': 10}
        )
        
        result = metadata.to_dict()
        
        assert result['model_type'] == 'lstm'
        assert result['symbol'] == 'GOOGL'
        assert result['trained_at'] == now.isoformat()
        assert result['data_hash'] == 'def456'
    
    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            'model_type': 'autoencoder',
            'symbol': 'MSFT',
            'trained_at': '2024-01-15T10:30:00',
            'data_hash': 'ghi789',
            'hyperparameters': {'encoding_dim': 8},
            'metrics': {'reconstruction_error': 0.05}
        }
        
        metadata = ModelMetadata.from_dict(data)
        
        assert metadata.model_type == 'autoencoder'
        assert metadata.symbol == 'MSFT'
        assert metadata.hyperparameters['encoding_dim'] == 8
        assert isinstance(metadata.trained_at, datetime)
    
    def test_metadata_is_expired_false(self):
        """Test that fresh metadata is not expired."""
        metadata = ModelMetadata(
            model_type='test',
            symbol='TEST',
            trained_at=datetime.utcnow(),
            data_hash='test123',
            hyperparameters={}
        )
        
        assert metadata.is_expired(max_age_hours=24) is False
    
    def test_metadata_is_expired_true(self):
        """Test that old metadata is expired."""
        old_time = datetime.utcnow() - timedelta(hours=48)
        metadata = ModelMetadata(
            model_type='test',
            symbol='TEST',
            trained_at=old_time,
            data_hash='test123',
            hyperparameters={}
        )
        
        assert metadata.is_expired(max_age_hours=24) is True
    
    def test_metadata_is_expired_custom_age(self):
        """Test expiration with custom max age."""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        metadata = ModelMetadata(
            model_type='test',
            symbol='TEST',
            trained_at=one_hour_ago,
            data_hash='test123',
            hyperparameters={}
        )
        
        # Should not be expired with 2 hour max age
        assert metadata.is_expired(max_age_hours=2) is False
        
        # Should be expired with 0.5 hour max age
        assert metadata.is_expired(max_age_hours=0) is True


class TestModelPersistenceManager:
    """Tests for ModelPersistenceManager class."""
    
    def test_initialization_default(self, temp_model_dir):
        """Test manager initialization with default directory."""
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        assert os.path.exists(manager.model_dir)
    
    def test_initialization_creates_directory(self, temp_model_dir):
        """Test that manager creates directory if it doesn't exist."""
        new_dir = os.path.join(temp_model_dir, 'new_models')
        manager = ModelPersistenceManager(model_dir=new_dir)
        
        assert os.path.exists(new_dir)
    
    def test_compute_data_hash_dataframe(self, sample_stock_data):
        """Test computing hash from DataFrame."""
        hash1 = ModelPersistenceManager.compute_data_hash(sample_stock_data)
        hash2 = ModelPersistenceManager.compute_data_hash(sample_stock_data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        
        # Hash should be string
        assert isinstance(hash1, str)
        assert len(hash1) == 16  # MD5 truncated
    
    def test_compute_data_hash_different_data(self, sample_stock_data):
        """Test that different data produces different hashes."""
        modified_data = sample_stock_data.copy()
        modified_data.loc[0, 'close'] = 999.99
        
        hash1 = ModelPersistenceManager.compute_data_hash(sample_stock_data)
        hash2 = ModelPersistenceManager.compute_data_hash(modified_data)
        
        assert hash1 != hash2
    
    def test_compute_data_hash_numpy(self):
        """Test computing hash from numpy array."""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        hash1 = ModelPersistenceManager.compute_data_hash(arr)
        hash2 = ModelPersistenceManager.compute_data_hash(arr)
        
        assert hash1 == hash2
    
    def test_save_and_load_sklearn_model(self, temp_model_dir):
        """Test saving and loading scikit-learn model."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Create and train a simple model
        model = IsolationForest(contamination=0.1, random_state=42)
        scaler = StandardScaler()
        
        X = np.random.randn(100, 5)
        scaler.fit(X)
        X_scaled = scaler.transform(X)
        model.fit(X_scaled)
        
        # Save model
        data_hash = 'test_hash_123'
        model_path = manager.save_sklearn_model(
            model=model,
            model_type='isolation_forest',
            symbol='SAVE_TEST',
            data_hash=data_hash,
            hyperparameters={'contamination': 0.1},
            scaler=scaler,
            metrics={'anomaly_rate': 0.1}
        )
        
        assert os.path.exists(model_path)
        
        # Load model
        loaded_model, loaded_scaler, metadata = manager.load_sklearn_model(
            model_type='isolation_forest',
            symbol='SAVE_TEST',
            data_hash=data_hash
        )
        
        assert loaded_model is not None
        assert loaded_scaler is not None
        assert metadata is not None
        assert metadata.model_type == 'isolation_forest'
        assert metadata.symbol == 'SAVE_TEST'
    
    def test_load_nonexistent_model(self, temp_model_dir):
        """Test loading a model that doesn't exist."""
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        model, scaler, metadata = manager.load_sklearn_model(
            model_type='nonexistent',
            symbol='FAKE'
        )
        
        assert model is None
        assert scaler is None
        assert metadata is None
    
    def test_load_expired_model(self, temp_model_dir):
        """Test that expired models are not loaded."""
        from sklearn.ensemble import IsolationForest
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Save a model
        model = IsolationForest(random_state=42)
        model.fit(np.random.randn(50, 3))
        
        manager.save_sklearn_model(
            model=model,
            model_type='if_expire_test',
            symbol='EXPIRE',
            data_hash='hash123',
            hyperparameters={}
        )
        
        # Manually modify metadata to be expired
        metadata_path = manager._get_metadata_path('if_expire_test', 'EXPIRE')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        old_time = datetime.utcnow() - timedelta(hours=48)
        metadata['trained_at'] = old_time.isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Load should return None for expired model
        loaded, _, _ = manager.load_sklearn_model(
            model_type='if_expire_test',
            symbol='EXPIRE',
            max_age_hours=24
        )
        
        assert loaded is None
    
    def test_load_with_wrong_data_hash(self, temp_model_dir):
        """Test that model is not loaded if data hash doesn't match."""
        from sklearn.ensemble import IsolationForest
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Save model with specific hash
        model = IsolationForest(random_state=42)
        model.fit(np.random.randn(50, 3))
        
        manager.save_sklearn_model(
            model=model,
            model_type='if_hash_test',
            symbol='HASH',
            data_hash='original_hash',
            hyperparameters={}
        )
        
        # Try to load with different hash
        loaded, _, _ = manager.load_sklearn_model(
            model_type='if_hash_test',
            symbol='HASH',
            data_hash='different_hash'
        )
        
        assert loaded is None
    
    def test_delete_model(self, temp_model_dir):
        """Test deleting a saved model."""
        from sklearn.ensemble import IsolationForest
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Save model
        model = IsolationForest(random_state=42)
        model.fit(np.random.randn(50, 3))
        
        manager.save_sklearn_model(
            model=model,
            model_type='delete_test',
            symbol='DELETE',
            data_hash='hash123',
            hyperparameters={}
        )
        
        # Verify it exists
        loaded, _, _ = manager.load_sklearn_model('delete_test', 'DELETE')
        assert loaded is not None
        
        # Delete it
        result = manager.delete_model('delete_test', 'DELETE')
        assert result is True
        
        # Verify it's gone
        loaded, _, _ = manager.load_sklearn_model('delete_test', 'DELETE')
        assert loaded is None
    
    def test_list_models(self, temp_model_dir):
        """Test listing all saved models."""
        from sklearn.ensemble import IsolationForest
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Save multiple models
        for symbol in ['AAPL', 'GOOGL', 'MSFT']:
            model = IsolationForest(random_state=42)
            model.fit(np.random.randn(50, 3))
            
            manager.save_sklearn_model(
                model=model,
                model_type='list_test',
                symbol=symbol,
                data_hash=f'hash_{symbol}',
                hyperparameters={}
            )
        
        # List models
        models = manager.list_models()
        
        assert len(models) == 3
        assert 'list_test_AAPL' in models
        assert 'list_test_GOOGL' in models
        assert 'list_test_MSFT' in models
    
    def test_cleanup_expired(self, temp_model_dir):
        """Test cleaning up expired models."""
        from sklearn.ensemble import IsolationForest
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Save models
        for i, symbol in enumerate(['OLD1', 'OLD2', 'NEW1']):
            model = IsolationForest(random_state=42)
            model.fit(np.random.randn(50, 3))
            
            manager.save_sklearn_model(
                model=model,
                model_type='cleanup_test',
                symbol=symbol,
                data_hash=f'hash_{symbol}',
                hyperparameters={}
            )
        
        # Make first two models expired
        for symbol in ['OLD1', 'OLD2']:
            metadata_path = manager._get_metadata_path('cleanup_test', symbol)
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            old_time = datetime.utcnow() - timedelta(hours=100)
            metadata['trained_at'] = old_time.isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        # Cleanup expired
        deleted_count = manager.cleanup_expired(max_age_hours=24)
        
        assert deleted_count == 2
        
        # Verify cleanup
        models = manager.list_models()
        assert len(models) == 1
        assert 'cleanup_test_NEW1' in models


class TestModelPersistenceIntegration:
    """Integration tests for model persistence with real ML models."""
    
    def test_full_workflow(self, sample_stock_data, temp_model_dir):
        """Test complete workflow: save, load, predict, update, delete."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        manager = ModelPersistenceManager(model_dir=temp_model_dir)
        
        # Prepare data
        X = sample_stock_data[['close', 'volume']].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        data_hash = manager.compute_data_hash(sample_stock_data)
        
        # Train and save
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_scaled)
        
        manager.save_sklearn_model(
            model=model,
            model_type='full_workflow',
            symbol='WORKFLOW',
            data_hash=data_hash,
            hyperparameters={'contamination': 0.1},
            scaler=scaler,
            metrics={'n_samples': len(X)}
        )
        
        # Load and verify
        loaded_model, loaded_scaler, metadata = manager.load_sklearn_model(
            model_type='full_workflow',
            symbol='WORKFLOW',
            data_hash=data_hash
        )
        
        assert loaded_model is not None
        
        # Make predictions with loaded model
        X_scaled_new = loaded_scaler.transform(X)
        predictions = loaded_model.predict(X_scaled_new)
        
        assert len(predictions) == len(X)
        
        # Clean up
        manager.delete_model('full_workflow', 'WORKFLOW')
        
        # Verify deleted
        loaded, _, _ = manager.load_sklearn_model('full_workflow', 'WORKFLOW')
        assert loaded is None
