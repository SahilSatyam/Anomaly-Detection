from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from typing import Optional, List
import logging
from .models import Base, Stock, StockPrice, Anomaly

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str = "postgresql://stockuser:Sahil1502@localhost:5432/stock_db"):
        """
        Initialize database connection
        
        Args:
            connection_string (str): PostgreSQL connection string
        """
        try:
            self.engine = create_engine(connection_string)
            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

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
            return stock
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error in get_or_create_stock: {str(e)}")
            raise
        finally:
            session.close()

    def store_stock_data(self, symbol: str, df: pd.DataFrame) -> None:
        """
        Store stock price data in database
        
        Args:
            symbol (str): Stock symbol
            df (pd.DataFrame): DataFrame containing price data
        """
        session = self.Session()
        try:
            stock = self.get_or_create_stock(symbol)
            
            for _, row in df.iterrows():
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
            
            session.commit()
            logger.info(f"Successfully stored {len(df)} records for {symbol}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing stock data: {str(e)}")
            raise
        finally:
            session.close()

    def store_anomaly(self, stock_id: int, date: str, anomaly_type: str, 
                     detection_method: str, score: float, threshold: float) -> None:
        """
        Store detected anomaly in database
        
        Args:
            stock_id (int): ID of the stock
            date (str): Date of the anomaly
            anomaly_type (str): Type of anomaly
            detection_method (str): Method used for detection
            score (float): Anomaly score
            threshold (float): Detection threshold
        """
        session = self.Session()
        try:
            anomaly = Anomaly(
                stock_id=stock_id,
                date=date,
                anomaly_type=anomaly_type,
                detection_method=detection_method,
                score=score,
                threshold=threshold
            )
            session.add(anomaly)
            session.commit()
            logger.info(f"Successfully stored anomaly for stock_id {stock_id}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing anomaly: {str(e)}")
            raise
        finally:
            session.close()

    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve stock data from database
        
        Args:
            symbol (str): Stock symbol
            start_date (str, optional): Start date for data retrieval
            end_date (str, optional): End date for data retrieval
            
        Returns:
            pd.DataFrame: DataFrame containing stock data
        """
        session = self.Session()
        try:
            query = session.query(StockPrice).join(Stock).filter(Stock.symbol == symbol)
            
            if start_date:
                query = query.filter(StockPrice.date >= start_date)
            if end_date:
                query = query.filter(StockPrice.date <= end_date)
                
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
                
            return pd.DataFrame(data)
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving stock data: {str(e)}")
            raise
        finally:
            session.close()

    def get_anomalies(self, symbol: Optional[str] = None, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> List[dict]:
        """
        Retrieve anomalies from database
        
        Args:
            symbol (str, optional): Stock symbol to filter by
            start_date (str, optional): Start date for filtering
            end_date (str, optional): End date for filtering
            
        Returns:
            List[dict]: List of anomaly dictionaries
        """
        session = self.Session()
        try:
            query = session.query(Anomaly).join(Stock)
            
            if symbol:
                query = query.filter(Stock.symbol == symbol)
            if start_date:
                query = query.filter(Anomaly.date >= start_date)
            if end_date:
                query = query.filter(Anomaly.date <= end_date)
                
            results = query.all()
            return [anomaly.to_dict() for anomaly in results]
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving anomalies: {str(e)}")
            raise
        finally:
            session.close() 