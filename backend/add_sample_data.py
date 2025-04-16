from data_storage.database import DatabaseManager
from sqlalchemy import text

def add_sample_stocks():
    """Add sample stock data with company names and sectors"""
    db = DatabaseManager()
    session = db.Session()
    
    try:
        # Sample stock data
        sample_stocks = [
            {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology"},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "company_name": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "AMZN", "company_name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
            {"symbol": "META", "company_name": "Meta Platforms Inc.", "sector": "Communication Services"},
            {"symbol": "TSLA", "company_name": "Tesla Inc.", "sector": "Consumer Cyclical"},
            {"symbol": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology"},
        ]
        
        # Update existing stocks or insert new ones
        for stock in sample_stocks:
            # Check if stock exists
            result = session.execute(
                text("SELECT id FROM stocks WHERE symbol = :symbol"),
                {"symbol": stock["symbol"]}
            ).fetchone()
            
            if result:
                # Update existing stock
                session.execute(
                    text("""
                        UPDATE stocks 
                        SET company_name = :company_name, sector = :sector 
                        WHERE symbol = :symbol
                    """),
                    stock
                )
                print(f"Updated {stock['symbol']}")
            else:
                # Insert new stock
                session.execute(
                    text("""
                        INSERT INTO stocks (symbol, company_name, sector) 
                        VALUES (:symbol, :company_name, :sector)
                    """),
                    stock
                )
                print(f"Added {stock['symbol']}")
        
        session.commit()
        print("Sample stock data added successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding sample data: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    add_sample_stocks() 