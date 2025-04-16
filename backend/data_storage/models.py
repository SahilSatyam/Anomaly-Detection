from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_name = Column(String(100))
    sector = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prices = relationship("StockPrice", back_populates="stock")
    anomalies = relationship("Anomaly", back_populates="stock")

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")

class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    anomaly_type = Column(String(50), nullable=False)  # e.g., 'price', 'volume', 'hybrid'
    detection_method = Column(String(50), nullable=False)  # e.g., 'bollinger', 'zscore', 'isolation_forest', 'lstm'
    score = Column(Float, nullable=False)  # Anomaly score
    threshold = Column(Float, nullable=False)  # Threshold used for detection
    is_verified = Column(Boolean, default=False)  # Whether the anomaly has been verified
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="anomalies")

    def to_dict(self):
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'date': self.date.isoformat(),
            'anomaly_type': self.anomaly_type,
            'detection_method': self.detection_method,
            'score': self.score,
            'threshold': self.threshold,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat()
        } 