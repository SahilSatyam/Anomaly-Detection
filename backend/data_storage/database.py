import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
from .models import Base, Stock, StockPrice, Anomaly, AppSettings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default database URL (should be overridden by environment variable)
DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/stock_db")

# Default application settings
DEFAULT_SETTINGS = {
    "anomalyThreshold": {"value": "0.8", "type": "float", "description": "Anomaly detection threshold (0-1)"},
    "lookbackPeriod": {"value": "30", "type": "int", "description": "Lookback period in days"},
    "updateFrequency": {"value": "daily", "type": "string", "description": "Update frequency: hourly, daily, or weekly"}
}


class DatabaseManager:
    def __init__(self, connection_string: str = None):
        """
        Initialize database connection
        
        Args:
            connection_string (str): PostgreSQL connection string
        """
        try:
            # Use provided connection string or fall back to environment variable
            db_url = connection_string or DEFAULT_DATABASE_URL
            self.engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            self._initialize_default_settings()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def _initialize_default_settings(self) -> None:
        """Initialize default application settings if they don't exist"""
        session = self.Session()
        try:
            for key, config in DEFAULT_SETTINGS.items():
                existing = session.query(AppSettings).filter_by(key=key).first()
                if not existing:
                    setting = AppSettings(
                        key=key,
                        value=config["value"],
                        value_type=config["type"],
                        description=config["description"]
                    )
                    session.add(setting)
            session.commit()
            logger.info("Default settings initialized")
        except SQLAlchemyError as e:
            session.rollback()
            logger.warning(f"Could not initialize default settings: {str(e)}")
        finally:
            session.close()

    def get_or_create_stock(self, symbol: str, company_name: Optional[str] = None, sector: Optional[str] = None) -> Stock:
        """
        Get existing stock or create new one
        
        Args:
            symbol (str): Stock symbol
            company_name (str, optional): Company name
            sector (str, optional): Industry sector
            
        Returns:
            Stock: Stock object
        """
        session = self.Session()
        try:
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, company_name=company_name, sector=sector)
                session.add(stock)
                session.commit()
                logger.info(f"Created new stock: {symbol}")
            return stock
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error in get_or_create_stock: {str(e)}")
            raise
        finally:
            session.close()

    def upsert_stock_price(self, stock_id: int, date: datetime, open_price: float, 
                          high: float, low: float, close: float, volume: int) -> Tuple[bool, str]:
        """
        Insert or update a stock price record (upsert)
        
        Args:
            stock_id: ID of the stock
            date: Date of the price data
            open_price: Opening price
            high: High price
            low: Low price
            close: Closing price
            volume: Trading volume
            
        Returns:
            Tuple[bool, str]: (success, action) where action is 'inserted' or 'updated'
        """
        session = self.Session()
        try:
            # Check if record exists
            existing = session.query(StockPrice).filter_by(
                stock_id=stock_id, date=date
            ).first()
            
            if existing:
                # Update existing record
                existing.open = open_price
                existing.high = high
                existing.low = low
                existing.close = close
                existing.volume = volume
                session.commit()
                return (True, 'updated')
            else:
                # Insert new record
                price = StockPrice(
                    stock_id=stock_id,
                    date=date,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume
                )
                session.add(price)
                session.commit()
                return (True, 'inserted')
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error in upsert_stock_price: {str(e)}")
            raise
        finally:
            session.close()

    def store_stock_data(self, symbol: str, df: pd.DataFrame, upsert: bool = True) -> Dict[str, int]:
        """
        Store stock price data in database with deduplication
        
        Args:
            symbol (str): Stock symbol
            df (pd.DataFrame): DataFrame containing price data
            upsert (bool): If True, update existing records; if False, skip duplicates
            
        Returns:
            Dict[str, int]: Statistics about the operation (inserted, updated, skipped)
        """
        session = self.Session()
        stats = {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        try:
            stock = self.get_or_create_stock(symbol)
            
            for _, row in df.iterrows():
                try:
                    # Check for existing record
                    existing = session.query(StockPrice).filter_by(
                        stock_id=stock.id, date=row['date']
                    ).first()
                    
                    if existing:
                        if upsert:
                            # Update existing record
                            existing.open = row['open']
                            existing.high = row['high']
                            existing.low = row['low']
                            existing.close = row['close']
                            existing.volume = row['volume']
                            stats['updated'] += 1
                        else:
                            stats['skipped'] += 1
                    else:
                        # Insert new record
                        price = StockPrice(
                            stock_id=stock.id,
                            date=row['date'],
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            volume=row['volume']
                        )
                        session.add(price)
                        stats['inserted'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing row for {symbol}: {str(e)}")
                    stats['errors'] += 1
                    continue
            
            session.commit()
            logger.info(f"Stock data for {symbol}: inserted={stats['inserted']}, "
                       f"updated={stats['updated']}, skipped={stats['skipped']}, errors={stats['errors']}")
            return stats
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing stock data: {str(e)}")
            raise
        finally:
            session.close()

    def upsert_anomaly(self, stock_id: int, date: datetime, anomaly_type: str,
                      detection_method: str, score: float, threshold: float,
                      notes: Optional[str] = None) -> Tuple[int, str]:
        """
        Insert or update an anomaly record (upsert)
        
        Args:
            stock_id: ID of the stock
            date: Date of the anomaly
            anomaly_type: Type of anomaly
            detection_method: Method used for detection
            score: Anomaly score
            threshold: Detection threshold
            notes: Optional notes
            
        Returns:
            Tuple[int, str]: (anomaly_id, action) where action is 'inserted' or 'updated'
        """
        session = self.Session()
        try:
            # Check if record exists (same stock, date, and detection method)
            existing = session.query(Anomaly).filter_by(
                stock_id=stock_id, date=date, detection_method=detection_method
            ).first()
            
            if existing:
                # Update existing record
                existing.anomaly_type = anomaly_type
                existing.score = score
                existing.threshold = threshold
                if notes is not None:
                    existing.notes = notes
                session.commit()
                return (existing.id, 'updated')
            else:
                # Insert new record
                anomaly = Anomaly(
                    stock_id=stock_id,
                    date=date,
                    anomaly_type=anomaly_type,
                    detection_method=detection_method,
                    score=score,
                    threshold=threshold,
                    notes=notes
                )
                session.add(anomaly)
                session.commit()
                return (anomaly.id, 'inserted')
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error in upsert_anomaly: {str(e)}")
            raise
        finally:
            session.close()

    def store_anomaly(self, stock_id: int, date: str, anomaly_type: str, 
                     detection_method: str, score: float, threshold: float,
                     notes: Optional[str] = None) -> int:
        """
        Store detected anomaly in database (with upsert)
        
        Args:
            stock_id (int): ID of the stock
            date (str): Date of the anomaly
            anomaly_type (str): Type of anomaly
            detection_method (str): Method used for detection
            score (float): Anomaly score
            threshold (float): Detection threshold
            notes (str, optional): Notes about the anomaly
            
        Returns:
            int: ID of the stored/updated anomaly
        """
        anomaly_id, action = self.upsert_anomaly(
            stock_id=stock_id,
            date=date,
            anomaly_type=anomaly_type,
            detection_method=detection_method,
            score=score,
            threshold=threshold,
            notes=notes
        )
        logger.info(f"Anomaly {action} for stock_id {stock_id}: id={anomaly_id}")
        return anomaly_id

    def update_anomaly(self, anomaly_id: int, updates: Dict[str, Any]) -> Optional[Anomaly]:
        """
        Update an existing anomaly
        
        Args:
            anomaly_id: ID of the anomaly to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated Anomaly object or None if not found
        """
        session = self.Session()
        try:
            anomaly = session.query(Anomaly).filter_by(id=anomaly_id).first()
            if not anomaly:
                return None
            
            # Update allowed fields
            allowed_fields = ['anomaly_type', 'score', 'threshold', 'is_verified', 'notes']
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(anomaly, field, value)
            
            session.commit()
            logger.info(f"Updated anomaly {anomaly_id}")
            
            # Refresh and return
            session.refresh(anomaly)
            return anomaly
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating anomaly: {str(e)}")
            raise
        finally:
            session.close()

    def delete_anomaly(self, anomaly_id: int) -> bool:
        """
        Delete an anomaly by ID
        
        Args:
            anomaly_id: ID of the anomaly to delete
            
        Returns:
            True if deleted, False if not found
        """
        session = self.Session()
        try:
            anomaly = session.query(Anomaly).filter_by(id=anomaly_id).first()
            if not anomaly:
                return False
            
            session.delete(anomaly)
            session.commit()
            logger.info(f"Deleted anomaly {anomaly_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting anomaly: {str(e)}")
            raise
        finally:
            session.close()

    def get_anomaly_by_id(self, anomaly_id: int) -> Optional[dict]:
        """
        Get a single anomaly by ID
        
        Args:
            anomaly_id: ID of the anomaly
            
        Returns:
            Anomaly dictionary or None if not found
        """
        session = self.Session()
        try:
            anomaly = session.query(Anomaly).filter_by(id=anomaly_id).first()
            return anomaly.to_dict() if anomaly else None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving anomaly: {str(e)}")
            raise
        finally:
            session.close()

    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None,
                      limit: Optional[int] = None,
                      offset: int = 0) -> Tuple[pd.DataFrame, int]:
        """
        Retrieve stock data from database with pagination
        
        Args:
            symbol (str): Stock symbol
            start_date (str, optional): Start date for data retrieval
            end_date (str, optional): End date for data retrieval
            limit (int, optional): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            Tuple[pd.DataFrame, int]: DataFrame containing stock data and total count
        """
        session = self.Session()
        try:
            base_query = session.query(StockPrice).join(Stock).filter(Stock.symbol == symbol)
            
            if start_date:
                base_query = base_query.filter(StockPrice.date >= start_date)
            if end_date:
                base_query = base_query.filter(StockPrice.date <= end_date)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply ordering, offset and limit
            query = base_query.order_by(StockPrice.date)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            results = query.all()
            
            data = []
            for result in results:
                data.append({
                    'date': result.date,
                    'open': result.open,
                    'high': result.high,
                    'low': result.low,
                    'close': result.close,
                    'volume': result.volume
                })
                
            return pd.DataFrame(data), total_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving stock data: {str(e)}")
            raise
        finally:
            session.close()

    def get_anomalies(self, symbol: Optional[str] = None, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     limit: Optional[int] = None,
                     offset: int = 0,
                     detection_method: Optional[str] = None,
                     is_verified: Optional[bool] = None) -> Tuple[List[dict], int]:
        """
        Retrieve anomalies from database with pagination and filtering
        
        Args:
            symbol (str, optional): Stock symbol to filter by
            start_date (str, optional): Start date for filtering
            end_date (str, optional): End date for filtering
            limit (int, optional): Maximum number of records to return
            offset (int): Number of records to skip
            detection_method (str, optional): Filter by detection method
            is_verified (bool, optional): Filter by verification status
            
        Returns:
            Tuple[List[dict], int]: List of anomaly dictionaries and total count
        """
        session = self.Session()
        try:
            base_query = session.query(Anomaly).join(Stock)
            
            if symbol:
                base_query = base_query.filter(Stock.symbol == symbol)
            if start_date:
                base_query = base_query.filter(Anomaly.date >= start_date)
            if end_date:
                base_query = base_query.filter(Anomaly.date <= end_date)
            if detection_method:
                base_query = base_query.filter(Anomaly.detection_method == detection_method)
            if is_verified is not None:
                base_query = base_query.filter(Anomaly.is_verified == is_verified)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply ordering, offset and limit
            query = base_query.order_by(Anomaly.date.desc())
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            results = query.all()
            return [anomaly.to_dict() for anomaly in results], total_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving anomalies: {str(e)}")
            raise
        finally:
            session.close()

    # ============== Settings Management ==============
    
    def get_setting(self, key: str) -> Optional[Any]:
        """
        Get a single setting value
        
        Args:
            key: Setting key
            
        Returns:
            Setting value (converted to appropriate type) or None if not found
        """
        session = self.Session()
        try:
            setting = session.query(AppSettings).filter_by(key=key).first()
            if not setting:
                return None
            return self._convert_setting_value(setting.value, setting.value_type)
        except SQLAlchemyError as e:
            logger.error(f"Error getting setting: {str(e)}")
            raise
        finally:
            session.close()

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all application settings
        
        Returns:
            Dictionary of all settings with converted values
        """
        session = self.Session()
        try:
            settings = session.query(AppSettings).all()
            return {
                s.key: self._convert_setting_value(s.value, s.value_type)
                for s in settings
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting all settings: {str(e)}")
            raise
        finally:
            session.close()

    def update_setting(self, key: str, value: Any, value_type: Optional[str] = None) -> bool:
        """
        Update a setting value
        
        Args:
            key: Setting key
            value: New value
            value_type: Optional type hint ('string', 'int', 'float', 'bool', 'json')
            
        Returns:
            True if updated, False if setting not found
        """
        session = self.Session()
        try:
            setting = session.query(AppSettings).filter_by(key=key).first()
            if not setting:
                # Create new setting
                setting = AppSettings(
                    key=key,
                    value=str(value),
                    value_type=value_type or 'string'
                )
                session.add(setting)
            else:
                # Update existing
                setting.value = str(value)
                if value_type:
                    setting.value_type = value_type
            
            session.commit()
            logger.info(f"Updated setting: {key}={value}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating setting: {str(e)}")
            raise
        finally:
            session.close()

    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update multiple settings at once
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Dictionary of all current settings after update
        """
        session = self.Session()
        try:
            # Fetch all existing settings that match the provided keys at once
            keys = list(settings.keys())
            existing_settings = session.query(AppSettings).filter(AppSettings.key.in_(keys)).all()
            existing_map = {s.key: s for s in existing_settings}

            for key, value in settings.items():
                if key in existing_map:
                    setting = existing_map[key]
                    setting.value = str(value)
                else:
                    # Determine type
                    if isinstance(value, bool):
                        value_type = 'bool'
                    elif isinstance(value, int):
                        value_type = 'int'
                    elif isinstance(value, float):
                        value_type = 'float'
                    else:
                        value_type = 'string'
                    
                    setting = AppSettings(key=key, value=str(value), value_type=value_type)
                    session.add(setting)
            
            session.commit()
            logger.info(f"Updated {len(settings)} settings")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating settings: {str(e)}")
            raise
        finally:
            session.close()
        
        return self.get_all_settings()

    def _convert_setting_value(self, value: str, value_type: str) -> Any:
        """Convert setting value to appropriate Python type"""
        try:
            if value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'bool':
                return value.lower() in ('true', '1', 'yes')
            elif value_type == 'json':
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value

    # ============== Health Check ==============
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Dictionary with health status information
        """
        session = self.Session()
        try:
            # Test connection with simple query
            session.execute(text("SELECT 1"))
            
            # Get table statistics
            stock_count = session.query(Stock).count()
            price_count = session.query(StockPrice).count()
            anomaly_count = session.query(Anomaly).count()
            
            return {
                'status': 'healthy',
                'connected': True,
                'statistics': {
                    'stocks': stock_count,
                    'price_records': price_count,
                    'anomalies': anomaly_count
                }
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
        finally:
            session.close()
