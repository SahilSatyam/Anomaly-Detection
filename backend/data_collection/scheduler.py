from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from typing import List
from .fetch_data import StockDataFetcher
from ..data_storage.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIngestionScheduler:
    def __init__(self, symbols: List[str], db_manager: DatabaseManager):
        self.scheduler = BackgroundScheduler()
        self.symbols = symbols
        self.db_manager = db_manager
        self.data_fetcher = StockDataFetcher()

    def fetch_and_store_data(self):
        """
        Fetch latest stock data and store in database
        """
        try:
            logger.info("Starting daily data ingestion...")
            data = self.data_fetcher.fetch_multiple_stocks(self.symbols, period="1d", interval="1d")
            
            for symbol, df in data.items():
                if not df.empty:
                    # Store the data in the database
                    self.db_manager.store_stock_data(symbol, df)
                    logger.info(f"Successfully stored data for {symbol}")
                else:
                    logger.warning(f"No data fetched for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error in data ingestion: {str(e)}")

    def start_scheduler(self):
        """
        Start the scheduler for daily data ingestion
        """
        # Schedule job to run at market close (4:00 PM EST) on weekdays
        self.scheduler.add_job(
            self.fetch_and_store_data,
            trigger=CronTrigger(
                day_of_week='mon-fri',
                hour=16,
                minute=0,
                timezone='America/New_York'
            ),
            id='daily_data_ingestion',
            name='Daily stock data ingestion'
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")

    def stop_scheduler(self):
        """
        Stop the scheduler
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    # Example usage
    from ..data_storage.database import DatabaseManager
    
    # Initialize database manager (you'll need to implement this)
    db_manager = DatabaseManager()
    
    # List of stock symbols to monitor
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
    
    # Create and start scheduler
    scheduler = DataIngestionScheduler(symbols, db_manager)
    scheduler.start_scheduler() 