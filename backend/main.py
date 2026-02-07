"""
Stock Anomaly Detection API

A comprehensive API for detecting and managing anomalies in stock price data.
Built with FastAPI for high performance and automatic OpenAPI documentation.

Features:
- Stock data retrieval with pagination
- Anomaly detection and management
- Persistent settings storage
- Health monitoring endpoints
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import re

from data_storage.database import DatabaseManager
from data_storage.models import Stock, StockPrice, Anomaly

# Configure logging FIRST (before any imports that might use logger)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import anomaly detection modules
try:
    from anomaly_detection import (
        HybridAnomalyDetector,
        MLAnomalyDetector,
        LSTMAnomalyDetector,
        StatisticalAnomalyDetector,
        model_manager,
        FORECASTING_AVAILABLE
    )
    if FORECASTING_AVAILABLE:
        from anomaly_detection import TrendAnalyzer
    DETECTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Anomaly detection modules not fully available: {e}")
    DETECTION_AVAILABLE = False

# Import alert system
try:
    from alert_system import AlertManager, alert_manager
    ALERTS_AVAILABLE = alert_manager is not None
except ImportError as e:
    logger.warning(f"Alert system not available: {e}")
    ALERTS_AVAILABLE = False
    alert_manager = None


# ============== Enums ==============

class UpdateFrequency(str, Enum):
    """Valid update frequency options"""
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"


class AnomalyType(str, Enum):
    """Valid anomaly types"""
    price = "price"
    volume = "volume"
    hybrid = "hybrid"


class DetectionMethod(str, Enum):
    """Valid detection methods"""
    bollinger = "bollinger"
    zscore = "zscore"
    isolation_forest = "isolation_forest"
    lstm = "lstm"
    hybrid = "hybrid"


# ============== Pydantic Models ==============

# --- Request Models ---

class SettingsRequest(BaseModel):
    """Request model for updating settings"""
    anomalyThreshold: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Anomaly detection threshold (0-1)",
        example=0.8
    )
    lookbackPeriod: int = Field(
        ..., 
        ge=1, 
        le=365, 
        description="Lookback period in days (1-365)",
        example=30
    )
    updateFrequency: UpdateFrequency = Field(
        ..., 
        description="Update frequency: 'hourly', 'daily', or 'weekly'",
        example="daily"
    )

    class Config:
        schema_extra = {
            "example": {
                "anomalyThreshold": 0.8,
                "lookbackPeriod": 30,
                "updateFrequency": "daily"
            }
        }


class AnomalyCreateRequest(BaseModel):
    """Request model for creating an anomaly"""
    symbol: str = Field(..., min_length=1, max_length=5, description="Stock symbol")
    date: str = Field(..., description="Date in ISO format")
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    detection_method: DetectionMethod = Field(..., description="Detection method used")
    score: float = Field(..., ge=0.0, description="Anomaly score")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Detection threshold")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "date": "2024-01-15T00:00:00Z",
                "anomaly_type": "price",
                "detection_method": "zscore",
                "score": 3.5,
                "threshold": 0.8,
                "notes": "Significant price spike detected"
            }
        }


class AnomalyUpdateRequest(BaseModel):
    """Request model for updating an anomaly"""
    anomaly_type: Optional[AnomalyType] = Field(None, description="Type of anomaly")
    score: Optional[float] = Field(None, ge=0.0, description="Anomaly score")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection threshold")
    is_verified: Optional[bool] = Field(None, description="Verification status")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    class Config:
        schema_extra = {
            "example": {
                "is_verified": True,
                "notes": "Verified - caused by earnings release"
            }
        }


class DetectionMethodEnum(str, Enum):
    """Detection methods for the detection endpoint"""
    all = "all"
    statistical = "statistical"
    ml = "ml"
    lstm = "lstm"
    isolation_forest = "isolation_forest"
    hybrid = "hybrid"
    forecasting = "forecasting"


class DetectionRequest(BaseModel):
    """Request model for triggering anomaly detection"""
    symbol: str = Field(..., min_length=1, max_length=5, description="Stock symbol")
    methods: List[DetectionMethodEnum] = Field(
        default=[DetectionMethodEnum.all],
        description="Detection methods to use"
    )
    save_to_database: bool = Field(
        default=True,
        description="Save detected anomalies to database"
    )
    send_alerts: bool = Field(
        default=False,
        description="Send alerts for detected anomalies"
    )
    lookback_days: int = Field(
        default=365,
        ge=30,
        le=3650,
        description="Number of days of historical data to analyze"
    )
    threshold: float = Field(
        default=2.0,
        ge=0.5,
        le=5.0,
        description="Z-score threshold for anomaly detection"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "methods": ["all"],
                "save_to_database": True,
                "send_alerts": False,
                "lookback_days": 365,
                "threshold": 2.0
            }
        }


class DetectedAnomaly(BaseModel):
    """Single detected anomaly"""
    date: str
    score: float
    threshold: float
    method: str
    details: Dict[str, Any]


class DetectionResult(BaseModel):
    """Result from anomaly detection"""
    method: str
    anomalies_count: int
    anomalies: List[DetectedAnomaly]


class DetectionResponse(BaseModel):
    """Response from detection endpoint"""
    symbol: str
    analysis_period: Dict[str, str]
    total_anomalies: int
    results_by_method: Dict[str, DetectionResult]
    saved_to_database: int
    alerts_sent: bool
    processing_time_seconds: float


class AlertStatusResponse(BaseModel):
    """Alert system status"""
    email_enabled: bool
    slack_enabled: bool
    discord_enabled: bool
    custom_webhook_enabled: bool
    min_score_threshold: float
    recent_alerts_count: int
    recent_success_rate: float


class ModelStatusResponse(BaseModel):
    """Model cache status"""
    models: Dict[str, Dict[str, Any]]
    total_models: int


# --- Response Models ---

class SettingsResponse(BaseModel):
    """Response model for settings"""
    anomalyThreshold: float
    lookbackPeriod: int
    updateFrequency: str


class StockInfo(BaseModel):
    """Stock information model"""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology"
            }
        }


class StockListResponse(BaseModel):
    """Response model for stock list"""
    data: List[StockInfo]
    total: int


class StockPriceData(BaseModel):
    """Stock price data model"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int
    limit: Optional[int]
    offset: int
    has_more: bool


class StockDataResponse(BaseModel):
    """Response model for stock data with pagination"""
    data: List[StockPriceData]
    pagination: PaginationMeta


class AnomalyData(BaseModel):
    """Anomaly data model"""
    id: int
    stock_id: int
    date: str
    anomaly_type: str
    detection_method: str
    score: float
    threshold: float
    is_verified: bool
    notes: Optional[str]
    created_at: str
    updated_at: Optional[str]


class AnomalyResponse(BaseModel):
    """Response model for single anomaly"""
    data: dict


class AnomalyListResponse(BaseModel):
    """Response model for anomalies with pagination"""
    data: List[dict]
    pagination: PaginationMeta


class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str
    error_code: str
    timestamp: str

    class Config:
        schema_extra = {
            "example": {
                "detail": "Stock 'XYZ' not found in database",
                "error_code": "STOCK_NOT_FOUND",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    database: Dict[str, Any]


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    checks: Dict[str, bool]


# ============== Custom Exception Classes ==============

class StockNotFoundError(Exception):
    """Raised when a stock symbol is not found"""
    pass


class AnomalyNotFoundError(Exception):
    """Raised when an anomaly is not found"""
    pass


class InvalidDateFormatError(Exception):
    """Raised when date format is invalid"""
    pass


class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass


# ============== FastAPI Application ==============

app = FastAPI(
    title="Stock Anomaly Detection API",
    description="""
## Overview
A comprehensive API for detecting and managing anomalies in stock price data.

## Features
- **Stock Data**: Retrieve historical stock price data with pagination
- **Anomaly Detection**: Detect and manage anomalies using multiple methods
- **CRUD Operations**: Full create, read, update, delete support for anomalies
- **Settings Management**: Persistent configuration storage
- **Health Monitoring**: Health and readiness endpoints for monitoring

## Authentication
Currently, no authentication is required. Future versions will support API keys.

## Rate Limiting
No rate limiting is currently enforced.
    """,
    version="2.0.0",
    contact={
        "name": "Stock Anomaly Detection Team",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {"name": "Health", "description": "Health and readiness endpoints"},
        {"name": "Stocks", "description": "Stock information endpoints"},
        {"name": "Stock Data", "description": "Historical stock price data"},
        {"name": "Anomalies", "description": "Anomaly detection and management"},
        {"name": "Settings", "description": "Application configuration"},
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Exception Handlers ==============

@app.exception_handler(StockNotFoundError)
async def stock_not_found_handler(request, exc: StockNotFoundError):
    logger.warning(f"Stock not found: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "error_code": "STOCK_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(AnomalyNotFoundError)
async def anomaly_not_found_handler(request, exc: AnomalyNotFoundError):
    logger.warning(f"Anomaly not found: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "error_code": "ANOMALY_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(InvalidDateFormatError)
async def invalid_date_handler(request, exc: InvalidDateFormatError):
    logger.warning(f"Invalid date format: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_code": "INVALID_DATE_FORMAT",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(DatabaseConnectionError)
async def database_error_handler(request, exc: DatabaseConnectionError):
    logger.error(f"Database connection error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service is temporarily unavailable",
            "error_code": "DATABASE_UNAVAILABLE",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============== Utility Functions ==============

def validate_stock_symbol(symbol: str) -> str:
    """
    Validate and sanitize stock symbol
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        Sanitized uppercase symbol
        
    Raises:
        HTTPException: If symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol is required and must be a string"
        )
    
    # Remove whitespace and convert to uppercase
    symbol = symbol.strip().upper()
    
    # Validate format (1-5 alphanumeric characters)
    if not re.match(r'^[A-Z0-9]{1,5}$', symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stock symbol format. Must be 1-5 alphanumeric characters."
        )
    
    return symbol


def parse_iso_date(date_string: Optional[str], param_name: str) -> Optional[datetime]:
    """
    Parse ISO format date string
    
    Args:
        date_string: Date string to parse
        param_name: Parameter name for error messages
        
    Returns:
        Parsed datetime object or None
        
    Raises:
        InvalidDateFormatError: If date format is invalid
    """
    if not date_string:
        return None
        
    try:
        # Handle ISO format with or without timezone
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError as e:
        raise InvalidDateFormatError(
            f"Invalid date format for '{param_name}': '{date_string}'. "
            f"Expected ISO format (e.g., '2024-01-01' or '2024-01-01T00:00:00Z')"
        )


def get_database_session():
    """
    Get database session with error handling
    
    Returns:
        Database session
        
    Raises:
        DatabaseConnectionError: If connection fails
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    try:
        return db.Session()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise DatabaseConnectionError("Unable to connect to database")


# ============== Initialize Database ==============

try:
    db = DatabaseManager()
    logger.info("Database connection initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize database connection: {e}")
    db = None


# ============== Health Endpoints ==============

@app.get(
    "/api/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the health status of the API and its dependencies"
)
async def health_check():
    """
    Perform a comprehensive health check of the API.
    
    Returns information about:
    - API status
    - Database connectivity
    - Database statistics
    """
    db_health = db.health_check() if db else {"status": "disconnected", "connected": False}
    
    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "database": db_health
    }


@app.get(
    "/api/ready",
    tags=["Health"],
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Returns whether the API is ready to accept requests"
)
async def readiness_check():
    """
    Check if the API is ready to handle requests.
    
    Used by orchestration systems (Kubernetes, etc.) to determine
    if the service should receive traffic.
    """
    db_ready = db is not None and db.health_check().get("connected", False)
    
    return {
        "ready": db_ready,
        "checks": {
            "database": db_ready
        }
    }


# ============== Stock Endpoints ==============

@app.get(
    "/api/stocks",
    tags=["Stocks"],
    response_model=StockListResponse,
    summary="List all stocks",
    description="Retrieve a list of all available stocks in the database"
)
async def get_stocks():
    """
    Get list of all available stocks.
    
    Returns stock symbols along with company names and sectors.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    session = get_database_session()
    try:
        logger.info("Fetching list of stocks")
        stocks = session.query(Stock).order_by(Stock.symbol).all()
        
        result = {
            "data": [
                {
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "sector": stock.sector
                }
                for stock in stocks
            ],
            "total": len(stocks)
        }
        logger.info(f"Successfully retrieved {len(stocks)} stocks")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching stocks"
        )
    finally:
        session.close()


# ============== Stock Data Endpoints ==============

@app.get(
    "/api/stock-data",
    tags=["Stock Data"],
    response_model=StockDataResponse,
    summary="Get stock price data",
    description="Retrieve historical stock price data with optional date filtering and pagination"
)
async def get_stock_data(
    symbol: str = Query(
        ..., 
        description="Stock symbol (e.g., AAPL)",
        example="AAPL",
        min_length=1,
        max_length=5
    ),
    start: Optional[str] = Query(
        None, 
        description="Start date in ISO format",
        example="2024-01-01"
    ),
    end: Optional[str] = Query(
        None, 
        description="End date in ISO format",
        example="2024-12-31"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=10000,
        description="Maximum number of records to return (1-10000)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination"
    )
):
    """
    Get historical stock price data with pagination.
    
    - **symbol**: Stock ticker symbol (required)
    - **start**: Optional start date filter
    - **end**: Optional end date filter
    - **limit**: Optional maximum records (for pagination)
    - **offset**: Records to skip (for pagination)
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    # Validate inputs
    symbol = validate_stock_symbol(symbol)
    start_date = parse_iso_date(start, "start")
    end_date = parse_iso_date(end, "end")
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    session = get_database_session()
    try:
        logger.info(f"Fetching stock data for {symbol} (start={start}, end={end}, limit={limit}, offset={offset})")
        
        # Get stock
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise StockNotFoundError(f"Stock '{symbol}' not found in database")
        
        # Build query
        query = session.query(StockPrice).filter(StockPrice.stock_id == stock.id)
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(StockPrice.date)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        prices = query.all()
        
        # Calculate has_more
        has_more = (offset + len(prices)) < total_count
        
        result = {
            "data": [
                {
                    "date": price.date.isoformat(),
                    "open": float(price.open),
                    "high": float(price.high),
                    "low": float(price.low),
                    "close": float(price.close),
                    "volume": int(price.volume)
                }
                for price in prices
            ],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            }
        }
        
        logger.info(f"Successfully retrieved {len(prices)} of {total_count} price records for {symbol}")
        return result
        
    except StockNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching data for {symbol}"
        )
    finally:
        session.close()


# ============== Anomaly Endpoints ==============

@app.get(
    "/api/anomalies",
    tags=["Anomalies"],
    response_model=AnomalyListResponse,
    summary="List anomalies",
    description="Retrieve detected anomalies with filtering and pagination"
)
async def get_anomalies(
    symbol: str = Query(
        ..., 
        description="Stock symbol (e.g., AAPL)",
        example="AAPL"
    ),
    start: Optional[str] = Query(
        None, 
        description="Start date in ISO format",
        example="2024-01-01"
    ),
    end: Optional[str] = Query(
        None, 
        description="End date in ISO format",
        example="2024-12-31"
    ),
    detection_method: Optional[DetectionMethod] = Query(
        None,
        description="Filter by detection method"
    ),
    is_verified: Optional[bool] = Query(
        None,
        description="Filter by verification status"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=1000,
        description="Maximum number of records to return (1-1000)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination"
    )
):
    """
    Get detected anomalies for a stock with pagination.
    
    - **symbol**: Stock ticker symbol (required)
    - **start**: Optional start date filter
    - **end**: Optional end date filter
    - **detection_method**: Filter by detection method
    - **is_verified**: Filter by verification status
    - **limit**: Maximum records (for pagination)
    - **offset**: Records to skip (for pagination)
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    # Validate inputs
    symbol = validate_stock_symbol(symbol)
    start_date = parse_iso_date(start, "start")
    end_date = parse_iso_date(end, "end")
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    session = get_database_session()
    try:
        logger.info(f"Fetching anomalies for {symbol}")
        
        # Get stock
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise StockNotFoundError(f"Stock '{symbol}' not found in database")
        
        # Build query
        query = session.query(Anomaly).filter(Anomaly.stock_id == stock.id)
        if start_date:
            query = query.filter(Anomaly.date >= start_date)
        if end_date:
            query = query.filter(Anomaly.date <= end_date)
        if detection_method:
            query = query.filter(Anomaly.detection_method == detection_method.value)
        if is_verified is not None:
            query = query.filter(Anomaly.is_verified == is_verified)
        
        # Get total count
        total_count = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(Anomaly.date.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        anomalies = query.all()
        
        # Calculate has_more
        has_more = (offset + len(anomalies)) < total_count
        
        result = {
            "data": [anomaly.to_dict() for anomaly in anomalies],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            }
        }
        
        logger.info(f"Successfully retrieved {len(anomalies)} of {total_count} anomalies for {symbol}")
        return result
        
    except StockNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching anomalies for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching anomalies for {symbol}"
        )
    finally:
        session.close()


@app.get(
    "/api/anomalies/{anomaly_id}",
    tags=["Anomalies"],
    response_model=AnomalyResponse,
    summary="Get anomaly by ID",
    description="Retrieve a single anomaly by its ID"
)
async def get_anomaly_by_id(
    anomaly_id: int = Path(..., description="Anomaly ID", ge=1)
):
    """
    Get a single anomaly by its ID.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    anomaly = db.get_anomaly_by_id(anomaly_id)
    if not anomaly:
        raise AnomalyNotFoundError(f"Anomaly with ID {anomaly_id} not found")
    
    logger.info(f"Retrieved anomaly {anomaly_id}")
    return {"data": anomaly}


@app.post(
    "/api/anomalies",
    tags=["Anomalies"],
    response_model=AnomalyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create anomaly",
    description="Create a new anomaly record"
)
async def create_anomaly(
    anomaly: AnomalyCreateRequest = Body(..., description="Anomaly data")
):
    """
    Create a new anomaly record.
    
    If an anomaly with the same stock, date, and detection method already exists,
    it will be updated instead (upsert behavior).
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    # Validate symbol and get stock
    symbol = validate_stock_symbol(anomaly.symbol)
    
    session = get_database_session()
    try:
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise StockNotFoundError(f"Stock '{symbol}' not found in database")
        
        # Parse date
        anomaly_date = parse_iso_date(anomaly.date, "date")
        if not anomaly_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date is required"
            )
        
        # Create anomaly
        anomaly_id, action = db.upsert_anomaly(
            stock_id=stock.id,
            date=anomaly_date,
            anomaly_type=anomaly.anomaly_type.value,
            detection_method=anomaly.detection_method.value,
            score=anomaly.score,
            threshold=anomaly.threshold,
            notes=anomaly.notes
        )
        
        # Fetch and return the created anomaly
        created_anomaly = db.get_anomaly_by_id(anomaly_id)
        
        logger.info(f"Anomaly {action}: id={anomaly_id}")
        return {"data": created_anomaly}
        
    except StockNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error creating anomaly: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the anomaly"
        )
    finally:
        session.close()


@app.put(
    "/api/anomalies/{anomaly_id}",
    tags=["Anomalies"],
    response_model=AnomalyResponse,
    summary="Update anomaly",
    description="Update an existing anomaly record"
)
async def update_anomaly(
    anomaly_id: int = Path(..., description="Anomaly ID", ge=1),
    updates: AnomalyUpdateRequest = Body(..., description="Fields to update")
):
    """
    Update an existing anomaly.
    
    Only the provided fields will be updated. Omitted fields remain unchanged.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    # Build updates dict, excluding None values
    update_dict = {}
    if updates.anomaly_type is not None:
        update_dict['anomaly_type'] = updates.anomaly_type.value
    if updates.score is not None:
        update_dict['score'] = updates.score
    if updates.threshold is not None:
        update_dict['threshold'] = updates.threshold
    if updates.is_verified is not None:
        update_dict['is_verified'] = updates.is_verified
    if updates.notes is not None:
        update_dict['notes'] = updates.notes
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    try:
        updated_anomaly = db.update_anomaly(anomaly_id, update_dict)
        if not updated_anomaly:
            raise AnomalyNotFoundError(f"Anomaly with ID {anomaly_id} not found")
        
        # Fetch fresh data
        anomaly_data = db.get_anomaly_by_id(anomaly_id)
        
        logger.info(f"Updated anomaly {anomaly_id}")
        return {"data": anomaly_data}
        
    except AnomalyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating anomaly {anomaly_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the anomaly"
        )


@app.delete(
    "/api/anomalies/{anomaly_id}",
    tags=["Anomalies"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete anomaly",
    description="Delete an anomaly record"
)
async def delete_anomaly(
    anomaly_id: int = Path(..., description="Anomaly ID", ge=1)
):
    """
    Delete an anomaly by its ID.
    
    Returns 204 No Content on success.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    try:
        deleted = db.delete_anomaly(anomaly_id)
        if not deleted:
            raise AnomalyNotFoundError(f"Anomaly with ID {anomaly_id} not found")
        
        logger.info(f"Deleted anomaly {anomaly_id}")
        return None
        
    except AnomalyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting anomaly {anomaly_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the anomaly"
        )


# ============== Settings Endpoints ==============

@app.get(
    "/api/settings",
    tags=["Settings"],
    response_model=SettingsResponse,
    summary="Get settings",
    description="Retrieve current application settings"
)
async def get_settings():
    """
    Get current application settings.
    
    Settings are persisted in the database.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    try:
        settings = db.get_all_settings()
        logger.info("Fetching application settings")
        
        return {
            "anomalyThreshold": settings.get("anomalyThreshold", 0.8),
            "lookbackPeriod": settings.get("lookbackPeriod", 30),
            "updateFrequency": settings.get("updateFrequency", "daily")
        }
        
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching settings"
        )


@app.post(
    "/api/settings",
    tags=["Settings"],
    response_model=SettingsResponse,
    summary="Update settings",
    description="Update application settings"
)
async def update_settings(settings: SettingsRequest):
    """
    Update application settings.
    
    All settings are validated and persisted to the database.
    """
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    try:
        logger.info(f"Updating settings: threshold={settings.anomalyThreshold}, "
                    f"lookback={settings.lookbackPeriod}, frequency={settings.updateFrequency}")
        
        # Update settings in database
        db.update_settings({
            "anomalyThreshold": settings.anomalyThreshold,
            "lookbackPeriod": settings.lookbackPeriod,
            "updateFrequency": settings.updateFrequency.value
        })
        
        return {
            "anomalyThreshold": settings.anomalyThreshold,
            "lookbackPeriod": settings.lookbackPeriod,
            "updateFrequency": settings.updateFrequency.value
        }
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating settings"
        )


# ============== Detection Endpoints ==============

@app.post(
    "/api/detect-anomalies",
    tags=["Detection"],
    response_model=DetectionResponse,
    summary="Trigger anomaly detection",
    description="Manually trigger anomaly detection for a stock symbol"
)
async def detect_anomalies(request: DetectionRequest = Body(...)):
    """
    Trigger anomaly detection for a specific stock.
    
    This endpoint allows you to:
    - Run detection using multiple methods
    - Save detected anomalies to the database
    - Optionally send alerts for significant anomalies
    
    Detection methods available:
    - **statistical**: Bollinger Bands and Z-Score
    - **isolation_forest**: Isolation Forest ML model
    - **lstm**: LSTM neural network
    - **hybrid**: Combination of all methods
    - **forecasting**: ARIMA/Prophet time-series analysis (if available)
    """
    import time
    start_time = time.time()
    
    if db is None:
        raise DatabaseConnectionError("Database not initialized")
    
    if not DETECTION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anomaly detection modules not available"
        )
    
    # Validate symbol
    symbol = validate_stock_symbol(request.symbol)
    
    session = get_database_session()
    try:
        # Get stock
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise StockNotFoundError(f"Stock '{symbol}' not found in database")
        
        # Get historical data
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.lookback_days)
        
        query = session.query(StockPrice).filter(
            StockPrice.stock_id == stock.id,
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        ).order_by(StockPrice.date)
        
        prices = query.all()
        
        if len(prices) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient data for analysis. Found {len(prices)} records, need at least 30."
            )
        
        # Convert to DataFrame
        import pandas as pd
        data = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume
        } for p in prices])
        
        logger.info(f"Running anomaly detection for {symbol} with {len(data)} data points")
        
        # Run detection based on requested methods
        results_by_method = {}
        all_anomalies = []
        
        methods = [m.value for m in request.methods]
        run_all = 'all' in methods
        
        # Statistical methods
        if run_all or 'statistical' in methods:
            try:
                stat_detector = StatisticalAnomalyDetector(
                    window_size=20,
                    num_std=request.threshold
                )
                
                bollinger_anomalies = stat_detector.detect_bollinger_anomalies(data)
                zscore_anomalies = stat_detector.detect_zscore_anomalies(data)
                volume_anomalies = stat_detector.detect_volume_anomalies(data)
                
                stat_anomalies = bollinger_anomalies + zscore_anomalies + volume_anomalies
                
                results_by_method['statistical'] = {
                    'method': 'statistical',
                    'anomalies_count': len(stat_anomalies),
                    'anomalies': [
                        {
                            'date': str(a.date),
                            'score': a.score,
                            'threshold': a.threshold,
                            'method': a.method,
                            'details': a.details
                        }
                        for a in stat_anomalies
                    ]
                }
                all_anomalies.extend(stat_anomalies)
            except Exception as e:
                logger.warning(f"Statistical detection failed: {e}")
        
        # Isolation Forest
        if run_all or 'isolation_forest' in methods or 'ml' in methods:
            try:
                ml_detector = MLAnomalyDetector(contamination=0.1)
                if_anomalies = ml_detector.detect_isolation_forest_anomalies(data, symbol)
                
                results_by_method['isolation_forest'] = {
                    'method': 'isolation_forest',
                    'anomalies_count': len(if_anomalies),
                    'anomalies': [
                        {
                            'date': str(a.date),
                            'score': a.score,
                            'threshold': a.threshold,
                            'method': a.method,
                            'details': a.details
                        }
                        for a in if_anomalies
                    ]
                }
                all_anomalies.extend(if_anomalies)
            except Exception as e:
                logger.warning(f"Isolation Forest detection failed: {e}")
        
        # LSTM
        if run_all or 'lstm' in methods or 'ml' in methods:
            try:
                lstm_detector = LSTMAnomalyDetector(
                    sequence_length=10,
                    threshold=request.threshold
                )
                lstm_anomalies = lstm_detector.detect_lstm_anomalies(data, symbol)
                
                results_by_method['lstm'] = {
                    'method': 'lstm',
                    'anomalies_count': len(lstm_anomalies),
                    'anomalies': [
                        {
                            'date': str(a.date),
                            'score': a.score,
                            'threshold': a.threshold,
                            'method': a.method,
                            'details': a.details
                        }
                        for a in lstm_anomalies
                    ]
                }
                all_anomalies.extend(lstm_anomalies)
            except Exception as e:
                logger.warning(f"LSTM detection failed: {e}")
        
        # Forecasting (ARIMA/Prophet)
        if (run_all or 'forecasting' in methods) and FORECASTING_AVAILABLE:
            try:
                trend_analyzer = TrendAnalyzer(
                    use_arima=True,
                    use_prophet=True,
                    threshold_std=request.threshold
                )
                forecast_results = trend_analyzer.analyze(data)
                
                for method_name, method_anomalies in forecast_results.items():
                    results_by_method[method_name] = {
                        'method': method_name,
                        'anomalies_count': len(method_anomalies),
                        'anomalies': [
                            {
                                'date': str(a.date),
                                'score': a.score,
                                'threshold': a.threshold,
                                'method': a.method,
                                'details': a.details
                            }
                            for a in method_anomalies
                        ]
                    }
                    all_anomalies.extend(method_anomalies)
            except Exception as e:
                logger.warning(f"Forecasting detection failed: {e}")
        
        # Hybrid (if requested)
        if 'hybrid' in methods:
            try:
                hybrid_detector = HybridAnomalyDetector(
                    window_size=20,
                    num_std=request.threshold
                )
                consensus_anomalies = hybrid_detector.get_consensus_anomalies(data, min_methods=2)
                
                results_by_method['hybrid_consensus'] = {
                    'method': 'hybrid_consensus',
                    'anomalies_count': len(consensus_anomalies),
                    'anomalies': [
                        {
                            'date': str(a.date),
                            'score': a.score,
                            'threshold': a.threshold,
                            'method': a.method,
                            'details': a.details
                        }
                        for a in consensus_anomalies
                    ]
                }
                # Don't add to all_anomalies to avoid duplicates
            except Exception as e:
                logger.warning(f"Hybrid detection failed: {e}")
        
        # Save to database if requested
        saved_count = 0
        if request.save_to_database and all_anomalies:
            # Deduplicate by date and method
            seen = set()
            for anomaly in all_anomalies:
                key = (str(anomaly.date), anomaly.method)
                if key in seen:
                    continue
                seen.add(key)
                
                try:
                    anomaly_type = 'hybrid' if 'hybrid' in anomaly.method else 'price'
                    db.store_anomaly(
                        stock_id=stock.id,
                        date=anomaly.date,
                        anomaly_type=anomaly_type,
                        detection_method=anomaly.method,
                        score=anomaly.score,
                        threshold=anomaly.threshold
                    )
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Failed to save anomaly: {e}")
        
        # Send alerts if requested
        alerts_sent = False
        if request.send_alerts and all_anomalies and ALERTS_AVAILABLE and alert_manager:
            try:
                alert_results = alert_manager.send_alert(symbol, all_anomalies)
                alerts_sent = any(r.success for r in alert_results)
            except Exception as e:
                logger.warning(f"Failed to send alerts: {e}")
        
        processing_time = time.time() - start_time
        
        # Get date range from data
        analysis_period = {
            'start': data['date'].min().isoformat() if hasattr(data['date'].min(), 'isoformat') else str(data['date'].min()),
            'end': data['date'].max().isoformat() if hasattr(data['date'].max(), 'isoformat') else str(data['date'].max())
        }
        
        logger.info(f"Detection complete for {symbol}: {len(all_anomalies)} anomalies in {processing_time:.2f}s")
        
        return {
            'symbol': symbol,
            'analysis_period': analysis_period,
            'total_anomalies': len(all_anomalies),
            'results_by_method': results_by_method,
            'saved_to_database': saved_count,
            'alerts_sent': alerts_sent,
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except StockNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during anomaly detection: {str(e)}"
        )
    finally:
        session.close()


@app.get(
    "/api/detection/status",
    tags=["Detection"],
    summary="Detection system status",
    description="Get the status of the anomaly detection system"
)
async def get_detection_status():
    """
    Get the current status of the detection system.
    
    Returns information about available detection methods and model cache.
    """
    status_info = {
        'detection_available': DETECTION_AVAILABLE,
        'forecasting_available': FORECASTING_AVAILABLE if DETECTION_AVAILABLE else False,
        'alerts_available': ALERTS_AVAILABLE,
        'available_methods': []
    }
    
    if DETECTION_AVAILABLE:
        status_info['available_methods'] = [
            'statistical',
            'isolation_forest',
            'lstm',
            'hybrid'
        ]
        if FORECASTING_AVAILABLE:
            status_info['available_methods'].extend(['arima', 'prophet'])
    
    return status_info


@app.get(
    "/api/models",
    tags=["Detection"],
    response_model=ModelStatusResponse,
    summary="List cached models",
    description="Get list of cached ML models"
)
async def list_models():
    """
    List all cached ML models.
    
    Shows training date, expiration status, and model parameters.
    """
    if not DETECTION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection modules not available"
        )
    
    try:
        models = model_manager.list_models()
        return {
            'models': models,
            'total_models': len(models)
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model list"
        )


@app.delete(
    "/api/models/{model_type}/{symbol}",
    tags=["Detection"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cached model",
    description="Delete a cached model to force retraining"
)
async def delete_model(
    model_type: str = Path(..., description="Model type (e.g., 'isolation_forest', 'lstm')"),
    symbol: str = Path(..., description="Stock symbol")
):
    """
    Delete a cached model.
    
    This forces the model to be retrained on the next detection run.
    """
    if not DETECTION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection modules not available"
        )
    
    symbol = validate_stock_symbol(symbol)
    
    deleted = model_manager.delete_model(model_type, symbol)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_type}' for '{symbol}' not found"
        )
    
    return None


@app.post(
    "/api/models/cleanup",
    tags=["Detection"],
    summary="Cleanup expired models",
    description="Delete all expired cached models"
)
async def cleanup_models(max_age_hours: int = Query(24, ge=1, le=720)):
    """
    Cleanup expired models.
    
    Deletes all cached models older than the specified age.
    """
    if not DETECTION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection modules not available"
        )
    
    try:
        deleted_count = model_manager.cleanup_expired(max_age_hours)
        return {
            'deleted_count': deleted_count,
            'max_age_hours': max_age_hours
        }
    except Exception as e:
        logger.error(f"Error cleaning up models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during model cleanup"
        )


# ============== Alert Endpoints ==============

@app.get(
    "/api/alerts/status",
    tags=["Alerts"],
    response_model=AlertStatusResponse,
    summary="Alert system status",
    description="Get the status of the alert system"
)
async def get_alert_status():
    """
    Get the current status of the alert system.
    
    Shows which channels are enabled and recent alert statistics.
    """
    if not ALERTS_AVAILABLE or alert_manager is None:
        return {
            'email_enabled': False,
            'slack_enabled': False,
            'discord_enabled': False,
            'custom_webhook_enabled': False,
            'min_score_threshold': 1.5,
            'recent_alerts_count': 0,
            'recent_success_rate': 0.0
        }
    
    return alert_manager.get_status()


@app.get(
    "/api/alerts/history",
    tags=["Alerts"],
    summary="Alert history",
    description="Get recent alert history"
)
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = Query(None, description="Filter by channel")
):
    """
    Get recent alert history.
    """
    if not ALERTS_AVAILABLE or alert_manager is None:
        return {'history': [], 'total': 0}
    
    history = alert_manager.get_alert_history(limit=limit, channel=channel)
    return {
        'history': history,
        'total': len(history)
    }




@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Stock Anomaly Detection API v2.0.0 starting up")
    if db is None:
        logger.warning("Database connection not available at startup")
    else:
        logger.info("Database connection verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Stock Anomaly Detection API shutting down")