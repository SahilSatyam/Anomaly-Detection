"""
Database Migration Script

This script applies schema updates to an existing database.
Run this after updating the models to add new columns, constraints, and tables.

Usage:
    python migrate_schema.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/stock_db")


def get_engine():
    """Create database engine"""
    return create_engine(DATABASE_URL)


def table_exists(engine, table_name: str) -> bool:
    """Check if a table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def constraint_exists(engine, table_name: str, constraint_name: str) -> bool:
    """Check if a constraint exists"""
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def run_migrations():
    """Run all migrations"""
    engine = get_engine()
    
    logger.info("Starting database migrations...")
    
    with engine.connect() as conn:
        try:
            # ============== Migration 1: Add updated_at columns ==============
            logger.info("Checking for updated_at columns...")
            
            tables_needing_updated_at = ['stocks', 'stock_prices', 'anomalies']
            for table in tables_needing_updated_at:
                if table_exists(engine, table) and not column_exists(engine, table, 'updated_at'):
                    logger.info(f"Adding updated_at column to {table}")
                    conn.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    conn.commit()
                    logger.info(f"Added updated_at to {table}")
            
            # ============== Migration 2: Add notes column to anomalies ==============
            if table_exists(engine, 'anomalies') and not column_exists(engine, 'anomalies', 'notes'):
                logger.info("Adding notes column to anomalies")
                conn.execute(text("""
                    ALTER TABLE anomalies 
                    ADD COLUMN notes TEXT
                """))
                conn.commit()
                logger.info("Added notes column to anomalies")
            
            # ============== Migration 3: Add unique constraint to stock_prices ==============
            if table_exists(engine, 'stock_prices'):
                if not constraint_exists(engine, 'stock_prices', 'uq_stock_price_date'):
                    logger.info("Adding unique constraint to stock_prices (stock_id, date)")
                    try:
                        # First, remove any duplicates (keep the latest)
                        conn.execute(text("""
                            DELETE FROM stock_prices a USING stock_prices b
                            WHERE a.id < b.id 
                            AND a.stock_id = b.stock_id 
                            AND a.date = b.date
                        """))
                        conn.commit()
                        
                        # Add the constraint
                        conn.execute(text("""
                            ALTER TABLE stock_prices 
                            ADD CONSTRAINT uq_stock_price_date UNIQUE (stock_id, date)
                        """))
                        conn.commit()
                        logger.info("Added unique constraint uq_stock_price_date")
                    except SQLAlchemyError as e:
                        logger.warning(f"Could not add constraint uq_stock_price_date: {e}")
                        conn.rollback()
            
            # ============== Migration 4: Add unique constraint to anomalies ==============
            if table_exists(engine, 'anomalies'):
                if not constraint_exists(engine, 'anomalies', 'uq_anomaly_stock_date_method'):
                    logger.info("Adding unique constraint to anomalies (stock_id, date, detection_method)")
                    try:
                        # First, remove any duplicates (keep the latest)
                        conn.execute(text("""
                            DELETE FROM anomalies a USING anomalies b
                            WHERE a.id < b.id 
                            AND a.stock_id = b.stock_id 
                            AND a.date = b.date
                            AND a.detection_method = b.detection_method
                        """))
                        conn.commit()
                        
                        # Add the constraint
                        conn.execute(text("""
                            ALTER TABLE anomalies 
                            ADD CONSTRAINT uq_anomaly_stock_date_method UNIQUE (stock_id, date, detection_method)
                        """))
                        conn.commit()
                        logger.info("Added unique constraint uq_anomaly_stock_date_method")
                    except SQLAlchemyError as e:
                        logger.warning(f"Could not add constraint uq_anomaly_stock_date_method: {e}")
                        conn.rollback()
            
            # ============== Migration 5: Create app_settings table ==============
            if not table_exists(engine, 'app_settings'):
                logger.info("Creating app_settings table")
                conn.execute(text("""
                    CREATE TABLE app_settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        value_type VARCHAR(20) NOT NULL DEFAULT 'string',
                        description VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                logger.info("Created app_settings table")
                
                # Insert default settings
                logger.info("Inserting default settings")
                conn.execute(text("""
                    INSERT INTO app_settings (key, value, value_type, description) VALUES
                    ('anomalyThreshold', '0.8', 'float', 'Anomaly detection threshold (0-1)'),
                    ('lookbackPeriod', '30', 'int', 'Lookback period in days'),
                    ('updateFrequency', 'daily', 'string', 'Update frequency: hourly, daily, or weekly')
                """))
                conn.commit()
                logger.info("Inserted default settings")
            
            # ============== Migration 6: Add indexes ==============
            indexes_to_create = [
                ('ix_stock_prices_stock_date', 'stock_prices', 'stock_id, date'),
                ('ix_anomalies_stock_date', 'anomalies', 'stock_id, date'),
                ('ix_stocks_symbol', 'stocks', 'symbol'),
                ('ix_stock_prices_date', 'stock_prices', 'date'),
                ('ix_anomalies_date', 'anomalies', 'date'),
                ('ix_app_settings_key', 'app_settings', 'key'),
            ]
            
            for index_name, table_name, columns in indexes_to_create:
                if table_exists(engine, table_name):
                    try:
                        # Check if index exists
                        result = conn.execute(text(f"""
                            SELECT 1 FROM pg_indexes 
                            WHERE indexname = '{index_name}'
                        """))
                        if not result.fetchone():
                            logger.info(f"Creating index {index_name} on {table_name}({columns})")
                            conn.execute(text(f"""
                                CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})
                            """))
                            conn.commit()
                            logger.info(f"Created index {index_name}")
                    except SQLAlchemyError as e:
                        logger.warning(f"Could not create index {index_name}: {e}")
                        conn.rollback()
            
            logger.info("All migrations completed successfully!")
            
        except SQLAlchemyError as e:
            logger.error(f"Migration failed: {e}")
            conn.rollback()
            sys.exit(1)


if __name__ == "__main__":
    run_migrations()
