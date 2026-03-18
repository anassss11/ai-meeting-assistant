"""
Tests for BART metrics endpoint and tracking.

Tests cover metrics tracking in FallbackHandler and the /metrics/bart endpoint.
"""

import pytest
from unittest.mock import Mock, patch
from bart_fallback import FallbackHandler
from bart_config import BARTConfig


class TestFallbackHandlerMetrics:
    """Tests for metrics tracking in FallbackHandler."""
    
    def test_metrics_initialization(self):
        """Test that metrics are initialized to zero."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        assert handler.total_requests == 0
        assert handler.bart_requests == 0
        assert handler.fallback_requests == 0
        assert handler.error_count == 0
    
    def test_record_bart_request(self):
        """Test recording a successful BART request."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_bart_request()
        
        assert handler.total_requests == 1
        assert handler.bart_requests == 1
        assert handler.fallback_requests == 0
    
    def test_record_fallback_request(self):
        """Test recording a fallback request."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_fallback_request()
        
        assert handler.total_requests == 1
        assert handler.bart_requests == 0
        assert handler.fallback_requests == 1
    
    def test_record_multiple_requests(self):
        """Test recording multiple requests."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_bart_request()
        handler.record_bart_request()
        handler.record_fallback_request()
        handler.record_bart_request()
        
        assert handler.total_requests == 4
        assert handler.bart_requests == 3
        assert handler.fallback_requests == 1
    
    def test_get_metrics_returns_dict(self):
        """Test that get_metrics returns a dictionary."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        metrics = handler.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "bart_requests" in metrics
        assert "fallback_requests" in metrics
        assert "error_count" in metrics
        assert "fallback_rate" in metrics
    
    def test_get_metrics_initial_values(self):
        """Test initial metrics values."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        metrics = handler.get_metrics()
        
        assert metrics["total_requests"] == 0
        assert metrics["bart_requests"] == 0
        assert metrics["fallback_requests"] == 0
        assert metrics["error_count"] == 0
        assert metrics["fallback_rate"] == 0.0
    
    def test_fallback_rate_calculation_all_bart(self):
        """Test fallback rate when all requests are BART."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_bart_request()
        handler.record_bart_request()
        handler.record_bart_request()
        
        metrics = handler.get_metrics()
        
        assert metrics["fallback_rate"] == 0.0
    
    def test_fallback_rate_calculation_all_fallback(self):
        """Test fallback rate when all requests are fallback."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_fallback_request()
        handler.record_fallback_request()
        
        metrics = handler.get_metrics()
        
        assert metrics["fallback_rate"] == 1.0
    
    def test_fallback_rate_calculation_mixed(self):
        """Test fallback rate with mixed requests."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_bart_request()
        handler.record_bart_request()
        handler.record_fallback_request()
        
        metrics = handler.get_metrics()
        
        # 1 fallback out of 3 total = 0.333...
        assert abs(metrics["fallback_rate"] - (1.0 / 3.0)) < 0.001
    
    def test_error_count_tracking(self):
        """Test that error count is tracked in metrics."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        # Simulate errors
        handler.error_count = 5
        
        metrics = handler.get_metrics()
        
        assert metrics["error_count"] == 5
    
    def test_metrics_with_errors_and_requests(self):
        """Test metrics with both errors and requests."""
        config = BARTConfig()
        handler = FallbackHandler(config)
        
        handler.record_bart_request()
        handler.record_bart_request()
        handler.record_fallback_request()
        handler.error_count = 1
        
        metrics = handler.get_metrics()
        
        assert metrics["total_requests"] == 3
        assert metrics["bart_requests"] == 2
        assert metrics["fallback_requests"] == 1
        assert metrics["error_count"] == 1
        assert abs(metrics["fallback_rate"] - (1.0 / 3.0)) < 0.001


class TestMetricsEndpoint:
    """Tests for the /metrics/bart endpoint."""
    
    def test_metrics_endpoint_returns_metrics(self):
        """Test that /metrics/bart endpoint returns metrics."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/metrics/bart")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_requests" in data
        assert "bart_requests" in data
        assert "fallback_requests" in data
        assert "error_count" in data
        assert "fallback_rate" in data
    
    def test_metrics_endpoint_initial_state(self):
        """Test metrics endpoint returns zeros initially."""
        from fastapi.testclient import TestClient
        from main import app, fallback_handler
        
        # Reset metrics
        fallback_handler.total_requests = 0
        fallback_handler.bart_requests = 0
        fallback_handler.fallback_requests = 0
        fallback_handler.error_count = 0
        
        client = TestClient(app)
        response = client.get("/metrics/bart")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requests"] == 0
        assert data["bart_requests"] == 0
        assert data["fallback_requests"] == 0
        assert data["error_count"] == 0
        assert data["fallback_rate"] == 0.0
    
    def test_metrics_endpoint_after_requests(self):
        """Test metrics endpoint after recording requests."""
        from fastapi.testclient import TestClient
        from main import app, fallback_handler
        
        # Reset and record some requests
        fallback_handler.total_requests = 0
        fallback_handler.bart_requests = 0
        fallback_handler.fallback_requests = 0
        fallback_handler.error_count = 0
        
        fallback_handler.record_bart_request()
        fallback_handler.record_bart_request()
        fallback_handler.record_fallback_request()
        
        client = TestClient(app)
        response = client.get("/metrics/bart")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requests"] == 3
        assert data["bart_requests"] == 2
        assert data["fallback_requests"] == 1
        assert abs(data["fallback_rate"] - (1.0 / 3.0)) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
