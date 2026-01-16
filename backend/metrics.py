"""
Prometheus Metrics Module

Provides metrics collection and export for monitoring.
Integrates with FastAPI for automatic HTTP metrics.
"""

import os
import time
from functools import wraps
from typing import Callable, Optional
import logging

# Check if prometheus_client is available
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        Summary,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        multiprocess,
        REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed. Metrics will be disabled.")

logger = logging.getLogger(__name__)


# ==================== Metric Definitions ====================

if PROMETHEUS_AVAILABLE:
    # HTTP Request Metrics
    HTTP_REQUESTS_TOTAL = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )

    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )

    HTTP_REQUESTS_IN_PROGRESS = Gauge(
        'http_requests_in_progress',
        'Number of HTTP requests in progress',
        ['method', 'endpoint']
    )

    # Database Metrics
    DB_QUERIES_TOTAL = Counter(
        'db_queries_total',
        'Total database queries',
        ['operation', 'table']
    )

    DB_QUERY_DURATION_SECONDS = Histogram(
        'db_query_duration_seconds',
        'Database query duration in seconds',
        ['operation', 'table'],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
    )

    DB_CONNECTION_POOL_SIZE = Gauge(
        'db_connection_pool_size',
        'Database connection pool size'
    )

    DB_CONNECTION_POOL_USED = Gauge(
        'db_connection_pool_used',
        'Database connections in use'
    )

    # Anomaly Detection Metrics
    DETECTION_RUNS_TOTAL = Counter(
        'anomaly_detection_runs_total',
        'Total anomaly detection runs',
        ['method', 'symbol', 'status']
    )

    DETECTION_DURATION_SECONDS = Histogram(
        'anomaly_detection_duration_seconds',
        'Anomaly detection duration in seconds',
        ['method', 'symbol'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
    )

    ANOMALIES_DETECTED_TOTAL = Counter(
        'anomalies_detected_total',
        'Total anomalies detected',
        ['method', 'symbol', 'severity']
    )

    # Model Metrics
    MODEL_TRAINING_DURATION_SECONDS = Histogram(
        'model_training_duration_seconds',
        'Model training duration in seconds',
        ['model_type', 'symbol'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
    )

    MODEL_CACHE_HITS = Counter(
        'model_cache_hits_total',
        'Model cache hits',
        ['model_type']
    )

    MODEL_CACHE_MISSES = Counter(
        'model_cache_misses_total',
        'Model cache misses',
        ['model_type']
    )

    MODELS_IN_CACHE = Gauge(
        'models_in_cache',
        'Number of models in cache',
        ['model_type']
    )

    # Alert Metrics
    ALERTS_SENT_TOTAL = Counter(
        'alerts_sent_total',
        'Total alerts sent',
        ['channel', 'status']
    )

    # Application Info
    APP_INFO = Info(
        'app',
        'Application information'
    )

    # Stock Data Metrics
    STOCK_DATA_FETCHED_TOTAL = Counter(
        'stock_data_fetched_total',
        'Total stock data points fetched',
        ['symbol']
    )

    STOCKS_TRACKED = Gauge(
        'stocks_tracked_total',
        'Number of stocks being tracked'
    )


# ==================== Metric Functions ====================

def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track an HTTP request"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()
    
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_db_query(operation: str, table: str, duration: float):
    """Track a database query"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    DB_QUERIES_TOTAL.labels(
        operation=operation,
        table=table
    ).inc()
    
    DB_QUERY_DURATION_SECONDS.labels(
        operation=operation,
        table=table
    ).observe(duration)


def track_detection(method: str, symbol: str, status: str, duration: float, anomaly_count: int = 0):
    """Track an anomaly detection run"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    DETECTION_RUNS_TOTAL.labels(
        method=method,
        symbol=symbol,
        status=status
    ).inc()
    
    DETECTION_DURATION_SECONDS.labels(
        method=method,
        symbol=symbol
    ).observe(duration)
    
    if anomaly_count > 0:
        ANOMALIES_DETECTED_TOTAL.labels(
            method=method,
            symbol=symbol,
            severity='detected'
        ).inc(anomaly_count)


def track_model_training(model_type: str, symbol: str, duration: float):
    """Track model training"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    MODEL_TRAINING_DURATION_SECONDS.labels(
        model_type=model_type,
        symbol=symbol
    ).observe(duration)


def track_model_cache(model_type: str, hit: bool):
    """Track model cache hit/miss"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    if hit:
        MODEL_CACHE_HITS.labels(model_type=model_type).inc()
    else:
        MODEL_CACHE_MISSES.labels(model_type=model_type).inc()


def track_alert(channel: str, success: bool):
    """Track alert sending"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    ALERTS_SENT_TOTAL.labels(
        channel=channel,
        status='success' if success else 'failure'
    ).inc()


def set_app_info(version: str, environment: str = 'production'):
    """Set application info"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    APP_INFO.info({
        'version': version,
        'environment': environment,
        'python_version': os.sys.version.split()[0]
    })


def update_stock_count(count: int):
    """Update tracked stocks count"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    STOCKS_TRACKED.set(count)


# ==================== Decorators ====================

def track_time(metric_name: str = 'function_duration'):
    """Decorator to track function execution time"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Log to generic histogram if specific not provided
                return result
            except Exception as e:
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                return result
            except Exception as e:
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# ==================== FastAPI Integration ====================

def get_metrics():
    """Get all metrics in Prometheus format"""
    if not PROMETHEUS_AVAILABLE:
        return "# Prometheus metrics not available\n", "text/plain"
    
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


def create_metrics_endpoint(app):
    """
    Add /metrics endpoint to FastAPI application.
    
    Usage:
        from metrics import create_metrics_endpoint
        create_metrics_endpoint(app)
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus not available, /metrics endpoint not created")
        return
    
    from fastapi import Response
    
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        content, content_type = get_metrics()
        return Response(content=content, media_type=content_type)
    
    logger.info("Prometheus metrics endpoint created at /metrics")


class PrometheusMiddleware:
    """
    ASGI Middleware for automatic HTTP metrics collection.
    
    Usage:
        from metrics import PrometheusMiddleware
        app.add_middleware(PrometheusMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not PROMETHEUS_AVAILABLE:
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        
        # Normalize path for metrics (remove IDs, etc.)
        endpoint = self._normalize_path(path)
        
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=method,
            endpoint=endpoint
        ).inc()
        
        start_time = time.time()
        status_code = 500  # Default in case of error
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            
            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
                endpoint=endpoint
            ).dec()
            
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality"""
        import re
        
        # Replace numeric IDs with placeholder
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace UUIDs with placeholder
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path,
            flags=re.IGNORECASE
        )
        
        return path
