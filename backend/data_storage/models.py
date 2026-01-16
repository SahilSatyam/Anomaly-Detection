from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """Stock entity representing a tradeable security"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(100))
    sector = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="stock", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_name': self.company_name,
            'sector': self.sector,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StockPrice(Base):
    """Stock price data for a specific date"""
    __tablename__ = 'stock_prices'
    
    # Add unique constraint to prevent duplicate prices for same stock+date
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uq_stock_price_date'),
        Index('ix_stock_prices_stock_date', 'stock_id', 'date'),
    )
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    def to_dict(self):
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'date': self.date.isoformat() if self.date else None,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Anomaly(Base):
    """Detected anomaly in stock data"""
    __tablename__ = 'anomalies'
    
    # Add unique constraint to prevent duplicate anomalies for same stock+date+method
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', 'detection_method', name='uq_anomaly_stock_date_method'),
        Index('ix_anomalies_stock_date', 'stock_id', 'date'),
    )
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)  # e.g., 'price', 'volume', 'hybrid'
    detection_method = Column(String(50), nullable=False)  # e.g., 'bollinger', 'zscore', 'isolation_forest', 'lstm'
    score = Column(Float, nullable=False)  # Anomaly score
    threshold = Column(Float, nullable=False)  # Threshold used for detection
    is_verified = Column(Boolean, default=False)  # Whether the anomaly has been verified
    notes = Column(Text, nullable=True)  # User notes about the anomaly
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="anomalies")

    def to_dict(self):
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'date': self.date.isoformat() if self.date else None,
            'anomaly_type': self.anomaly_type,
            'detection_method': self.detection_method,
            'score': self.score,
            'threshold': self.threshold,
            'is_verified': self.is_verified,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AppSettings(Base):
    """Application settings storage"""
    __tablename__ = 'app_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False, default='string')  # string, int, float, bool, json
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }