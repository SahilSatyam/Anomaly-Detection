import sys
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from data_storage.database import DatabaseManager
from data_storage.models import Stock

def fetch_and_store_historical_data():
    """Fetch historical data for sample stocks and store in database"""
    db = DatabaseManager()
    session = db.Session()
    
    try:
        # Get all stocks from database
        stocks = session.query(Stock).all()
        
        if not stocks:
            print("No stocks found in database. Please run add_sample_data.py first.")
            return
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 3)  # 3 years of data
        
        for stock in stocks:
            try:
                print(f"Fetching data for {stock.symbol}...")
                
                # Fetch data from Yahoo Finance
                ticker = yf.Ticker(stock.symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    print(f"No data available for {stock.symbol}")
                    continue
                
                # Reset index to make date a column
                df = df.reset_index()
                
                # Rename columns to match our schema
                df = df.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                # Store data in database
                db.store_stock_data(stock.symbol, df)
                print(f"Stored {len(df)} records for {stock.symbol}")
                
            except Exception as e:
                print(f"Error processing {stock.symbol}: {str(e)}")
                continue
        
        print("Historical data collection completed successfully")
        
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    try:
        # First, make sure yfinance is installed
        import importlib
        if importlib.util.find_spec("yfinance") is None:
            print("Installing required package: yfinance")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
            print("yfinance installed successfully")
        
        fetch_and_store_historical_data()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure you have installed all required packages:")
        print("pip install yfinance pandas sqlalchemy psycopg2-binary") 