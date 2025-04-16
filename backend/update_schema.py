from sqlalchemy import text
from data_storage.database import DatabaseManager

def update_schema():
    """Update the database schema to add missing columns"""
    db = DatabaseManager()
    session = db.Session()
    
    try:
        # Check if company_name column exists
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'company_name'
        """))
        
        if not result.fetchone():
            # Add company_name column
            session.execute(text("""
                ALTER TABLE stocks 
                ADD COLUMN company_name VARCHAR(100)
            """))
            print("Added company_name column to stocks table")
        
        # Check if sector column exists
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'sector'
        """))
        
        if not result.fetchone():
            # Add sector column
            session.execute(text("""
                ALTER TABLE stocks 
                ADD COLUMN sector VARCHAR(50)
            """))
            print("Added sector column to stocks table")
        
        session.commit()
        print("Schema update completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating schema: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    update_schema() 