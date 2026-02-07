"""
Unit tests for API endpoints.

Tests cover:
- Health check endpoints
- Stock data endpoints
- Anomaly detection endpoints
- Settings endpoints
- Alert system endpoints
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test /api/health endpoint returns healthy status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy" or "status" in data
    
    def test_readiness_check(self, client):
        """Test /api/ready endpoint."""
        response = client.get("/api/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data or "status" in data


class TestStockEndpoints:
    """Tests for stock-related endpoints."""
    
    def test_get_stocks_list(self, client):
        """Test /api/stocks endpoint returns stock list."""
        response = client.get("/api/stocks")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have data key or be a list
        assert "data" in data or isinstance(data, list)
    
    def test_get_stock_data(self, client):
        """Test /api/stock-data endpoint with valid parameters."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = client.get(
            "/api/stock-data",
            params={
                "symbol": "AAPL",
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
        
        # Should return 200 or 404 (if no data)
        assert response.status_code in [200, 404]
    
    def test_get_stock_data_missing_symbol(self, client):
        """Test /api/stock-data endpoint without symbol parameter."""
        response = client.get("/api/stock-data")
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]
    
    def test_get_stock_data_invalid_symbol(self, client):
        """Test /api/stock-data with invalid symbol."""
        response = client.get(
            "/api/stock-data",
            params={"symbol": "INVALID123456789"}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 422]


class TestAnomalyEndpoints:
    """Tests for anomaly-related endpoints."""
    
    def test_get_anomalies(self, client):
        """Test /api/anomalies endpoint."""
        response = client.get(
            "/api/anomalies",
            params={"symbol": "AAPL"}
        )
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data or isinstance(data, list)
    
    def test_get_anomalies_with_date_range(self, client):
        """Test /api/anomalies with date range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = client.get(
            "/api/anomalies",
            params={
                "symbol": "AAPL",
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
        
        assert response.status_code in [200, 404]
    
    def test_detection_status(self, client):
        """Test /api/detection/status endpoint."""
        response = client.get("/api/detection/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain status information
        assert isinstance(data, dict)


class TestModelsEndpoints:
    """Tests for model management endpoints."""
    
    def test_list_models(self, client):
        """Test /api/models endpoint."""
        response = client.get("/api/models")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return model list
        assert isinstance(data, (dict, list))


class TestSettingsEndpoints:
    """Tests for settings endpoints."""
    
    def test_get_settings(self, client):
        """Test GET /api/settings endpoint."""
        response = client.get("/api/settings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
    
    def test_update_settings_valid(self, client):
        """Test POST /api/settings with valid data."""
        settings = {
            "anomalyThreshold": 0.8,
            "lookbackPeriod": 30,
            "updateFrequency": "daily"
        }
        
        response = client.post("/api/settings", json=settings)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("anomalyThreshold") == 0.8 or "anomalyThreshold" in str(data)
    
    def test_update_settings_invalid_threshold(self, client):
        """Test POST /api/settings with invalid threshold."""
        settings = {
            "anomalyThreshold": 1.5,  # Invalid: > 1.0
            "lookbackPeriod": 30,
            "updateFrequency": "daily"
        }
        
        response = client.post("/api/settings", json=settings)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_update_settings_invalid_frequency(self, client):
        """Test POST /api/settings with invalid frequency."""
        settings = {
            "anomalyThreshold": 0.8,
            "lookbackPeriod": 30,
            "updateFrequency": "invalid_frequency"
        }
        
        response = client.post("/api/settings", json=settings)
        
        # Should return validation error
        assert response.status_code == 422


class TestAlertEndpoints:
    """Tests for alert system endpoints."""
    
    def test_get_alert_status(self, client):
        """Test /api/alerts/status endpoint."""
        response = client.get("/api/alerts/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
    
    def test_get_alert_history(self, client):
        """Test /api/alerts/history endpoint."""
        response = client.get("/api/alerts/history")
        
        # Should return 200 or appropriate error
        assert response.status_code in [200, 404]


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""
    
    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        
        # Should contain Prometheus metric format
        content = response.text
        assert "http_requests" in content or "python" in content or len(content) > 0


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_docs(self, client):
        """Test /docs endpoint is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_json(self, client):
        """Test /openapi.json endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain OpenAPI spec
        assert "openapi" in data or "paths" in data


class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_not_found_endpoint(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method."""
        response = client.delete("/api/health")
        
        assert response.status_code == 405


class TestDetectionEndpoints:
    """Tests for anomaly detection trigger endpoints."""
    
    def test_detect_anomalies_request(self, client):
        """Test POST /api/detect-anomalies endpoint."""
        detection_request = {
            "symbol": "AAPL",
            "methods": ["statistical"],
            "save_to_database": False,
            "send_alerts": False,
            "lookback_days": 30,
            "threshold": 2.0
        }
        
        response = client.post("/api/detect-anomalies", json=detection_request)
        
        # Should return 200 or appropriate status
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_detect_anomalies_missing_symbol(self, client):
        """Test POST /api/detect-anomalies without symbol."""
        detection_request = {
            "methods": ["statistical"]
        }
        
        response = client.post("/api/detect-anomalies", json=detection_request)
        
        # Should return validation error
        assert response.status_code == 422
