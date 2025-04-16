import yfinance as yf
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
import os
import pandas as pd

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_storage.database import DatabaseManager
from data_storage.models import Stock, StockPrice

# List of Magnificent 7 companies
COMPANIES = [
    {"symbol": "AAPL", "name": "Apple Inc."},
    {"symbol": "MSFT", "name": "Microsoft Corporation"},
    {"symbol": "GOOGL", "name": "Alphabet Inc."},
    {"symbol": "AMZN", "name": "Amazon.com Inc."},
    {"symbol": "NVDA", "name": "NVIDIA Corporation"},
    {"symbol": "META", "name": "Meta Platforms Inc."},
    {"symbol": "TSLA", "name": "Tesla Inc."}
]

def collect_daily_data():
    """
    Collect daily stock data for specified companies and store in database
    """
    print(f"Starting data collection at {datetime.now(pytz.timezone('Asia/Kolkata'))}")
    
    # Initialize database connection
    db = DatabaseManager()
    
    # Get today's date in EST (US/Eastern) as that's the timezone for US market
    est = pytz.timezone('US/Eastern')
    today = datetime.now(est).date()
    
    try:
        for company in COMPANIES:
            symbol = company["symbol"]
            print(f"Collecting data for {symbol}")
            
            # Get stock data using yfinance
            stock = yf.Ticker(symbol)
            
            # Get today's data
            hist = stock.history(period="1d")
            
            if not hist.empty:
                # Convert the data to our format
                df = pd.DataFrame({
                    'date': [today],
                    'open': [float(hist.iloc[-1]['Open'])],
                    'high': [float(hist.iloc[-1]['High'])],
                    'low': [float(hist.iloc[-1]['Low'])],
                    'close': [float(hist.iloc[-1]['Close'])],
                    'volume': [int(hist.iloc[-1]['Volume'])]
                })
                
                # Store in database
                db.store_stock_data(symbol, df)
                print(f"Successfully stored data for {symbol}")
            else:
                print(f"No data available for {symbol} today")
                
    except Exception as e:
        print(f"Error collecting data: {str(e)}")

def start_scheduler():
    """
    Start the scheduler to run data collection at 9:00 PM IST daily
    """
    scheduler = BackgroundScheduler()
    
    # Create a trigger for 9:00 PM IST
    # Note: APScheduler uses server's local time, so we need to convert IST to local time
    ist = pytz.timezone('Asia/Kolkata')
    trigger = CronTrigger(
        hour=21,  # 9 PM
        minute=0,
        timezone=ist
    )
    
    # Add the job to the scheduler
    scheduler.add_job(
        collect_daily_data,
        trigger=trigger,
        name='daily_stock_data_collection',
        misfire_grace_time=3600  # Allow the job to be run up to 1 hour late
    )
    
    # Start the scheduler
    scheduler.start()
    print("Scheduler started. Will collect data at 9:00 PM IST daily.")
    
    try:
        # Keep the script running
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")

if __name__ == "__main__":
    # Collect data immediately when script starts
    collect_daily_data()
    
    # Start the scheduler for subsequent runs
    start_scheduler() 