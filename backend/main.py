from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
from data_storage.database import DatabaseManager
from data_storage.models import Stock, StockPrice, Anomaly
import pandas as pd

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database manager
db = DatabaseManager()

@app.get("/api/stocks")
async def get_stocks():
    """Get list of available stocks"""
    session = db.Session()
    try:
        stocks = session.query(Stock).all()
        return {
            "data": [
                {
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "sector": stock.sector
                }
                for stock in stocks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/stock-data")
async def get_stock_data(symbol: str, start: Optional[str] = None, end: Optional[str] = None):
    """Get historical stock data"""
    session = db.Session()
    try:
        # Convert string dates to datetime
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00')) if start else None
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else None
        
        # Get stock
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Query stock prices
        query = session.query(StockPrice).filter(StockPrice.stock_id == stock.id)
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        
        # Order by date
        prices = query.order_by(StockPrice.date).all()
        
        return {
            "data": [
                {
                    "date": price.date.isoformat(),
                    "open": price.open,
                    "high": price.high,
                    "low": price.low,
                    "close": price.close,
                    "volume": price.volume
                }
                for price in prices
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/anomalies")
async def get_anomalies(symbol: str, start: Optional[str] = None, end: Optional[str] = None):
    """Get detected anomalies"""
    session = db.Session()
    try:
        # Convert string dates to datetime
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00')) if start else None
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else None
        
        # Get stock
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Query anomalies
        query = session.query(Anomaly).filter(Anomaly.stock_id == stock.id)
        if start_date:
            query = query.filter(Anomaly.date >= start_date)
        if end_date:
            query = query.filter(Anomaly.date <= end_date)
        
        # Order by date
        anomalies = query.order_by(Anomaly.date).all()
        
        return {
            "data": [anomaly.to_dict() for anomaly in anomalies]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/settings")
async def get_settings():
    """Get application settings"""
    return {
        "anomalyThreshold": 0.8,
        "lookbackPeriod": 30,
        "updateFrequency": "daily"
    }

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update application settings"""
    # TODO: Implement settings storage
    return settings 