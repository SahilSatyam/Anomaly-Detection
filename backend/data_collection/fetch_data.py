import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

class StockDataFetcher:
    def __init__(self):
        self.cache = {}

    def fetch_stock_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch stock data using yFinance API
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            period (str): Time period to fetch (e.g., '1d', '5d', '1mo', '1y')
            interval (str): Data interval (e.g., '1m', '5m', '1h', '1d')
            
        Returns:
            pd.DataFrame: DataFrame containing stock data
        """
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            # Reset index to make Date a column
            df.reset_index(inplace=True)
            
            # Rename columns to match our database schema
            df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_stocks(self, symbols: List[str], period: str = "1y", interval: str = "1d") -> dict:
        """
        Fetch data for multiple stock symbols
        
        Args:
            symbols (List[str]): List of stock symbols
            period (str): Time period to fetch
            interval (str): Data interval
            
        Returns:
            dict: Dictionary with symbols as keys and DataFrames as values
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.fetch_stock_data(symbol, period, interval)
        return results

if __name__ == "__main__":
    # Example usage
    fetcher = StockDataFetcher()
    symbols = ["AAPL", "GOOGL", "MSFT"]
    data = fetcher.fetch_multiple_stocks(symbols)
    
    for symbol, df in data.items():
        print(f"\nData for {symbol}:")
        print(df.head()) 