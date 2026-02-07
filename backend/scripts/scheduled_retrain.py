#!/usr/bin/env python
"""
Scheduled Model Retraining Script

This script handles automated retraining of anomaly detection models.
Can be run manually or scheduled via cron/Task Scheduler.

Usage:
    python scheduled_retrain.py [--symbol SYMBOL] [--model MODEL] [--all]
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from anomaly_detection.model_persistence import ModelPersistenceManager
from anomaly_detection.ml_models import MLAnomalyDetector, LSTMAnomalyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
MODEL_TYPES = ['isolation_forest', 'lstm']


def fetch_stock_data(symbol: str, days: int = 365):
    """Fetch historical stock data for training."""
    try:
        import yfinance as yf
        import pandas as pd
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f'{days}d')
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        
        # Add computed features
        df['returns'] = df['close'].pct_change().fillna(0)
        df['volatility'] = df['returns'].rolling(window=20).std().fillna(0)
        
        logger.info(f"Fetched {len(df)} rows for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        return None


def retrain_model(symbol: str, model_type: str, manager: ModelPersistenceManager) -> dict:
    """Retrain a single model."""
    result = {
        'symbol': symbol,
        'model_type': model_type,
        'status': 'pending',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Fetch fresh data
        data = fetch_stock_data(symbol, days=365)
        
        if data is None or len(data) < 100:
            result['status'] = 'skipped'
            result['error'] = 'Insufficient data'
            return result
        
        # Delete existing model
        manager.delete_model(model_type, symbol)
        
        # Retrain based on model type
        if model_type == 'isolation_forest':
            detector = MLAnomalyDetector(
                contamination=0.1,
                model_manager=manager
            )
            detector.fit(data, symbol=symbol)
            
        elif model_type == 'lstm':
            detector = LSTMAnomalyDetector(
                sequence_length=10,
                threshold=2.0,
                model_manager=manager
            )
            detector.fit(data, symbol=symbol, epochs=30, batch_size=32)
        
        result['status'] = 'success'
        result['samples_used'] = len(data)
        logger.info(f"✓ Retrained {model_type} for {symbol}")
        
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        logger.error(f"✗ Failed to retrain {model_type} for {symbol}: {e}")
    
    return result


def retrain_all(symbols: list = None, model_types: list = None):
    """Retrain all models for specified symbols."""
    symbols = symbols or DEFAULT_SYMBOLS
    model_types = model_types or MODEL_TYPES
    
    manager = ModelPersistenceManager()
    results = []
    
    total = len(symbols) * len(model_types)
    current = 0
    
    for symbol in symbols:
        for model_type in model_types:
            current += 1
            logger.info(f"[{current}/{total}] Retraining {model_type} for {symbol}...")
            
            result = retrain_model(symbol, model_type, manager)
            results.append(result)
    
    return results


def cleanup_expired(max_age_hours: int = 48):
    """Clean up expired models."""
    manager = ModelPersistenceManager()
    deleted = manager.cleanup_expired(max_age_hours)
    logger.info(f"Cleaned up {deleted} expired models")
    return deleted


def print_summary(results: list):
    """Print retraining summary."""
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print("\n" + "=" * 60)
    print("RETRAINING SUMMARY")
    print("=" * 60)
    print(f"  ✓ Success: {success}")
    print(f"  ✗ Failed:  {failed}")
    print(f"  ⊘ Skipped: {skipped}")
    print(f"  Total:     {len(results)}")
    
    if failed > 0:
        print("\nFailed models:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r['symbol']}/{r['model_type']}: {r.get('error', 'Unknown error')}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Model Retraining Script')
    parser.add_argument('--symbol', '-s', help='Specific symbol to retrain')
    parser.add_argument('--model', '-m', choices=MODEL_TYPES, help='Specific model type')
    parser.add_argument('--all', '-a', action='store_true', help='Retrain all models')
    parser.add_argument('--cleanup', '-c', action='store_true', help='Cleanup expired models')
    parser.add_argument('--max-age', type=int, default=48, help='Max age for cleanup (hours)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"MODEL RETRAINING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*60)
    
    if args.cleanup:
        cleanup_expired(args.max_age)
        return
    
    if args.symbol and args.model:
        # Retrain specific model
        manager = ModelPersistenceManager()
        result = retrain_model(args.symbol, args.model, manager)
        print_summary([result])
        
    elif args.all or (not args.symbol and not args.model):
        # Retrain all
        symbols = [args.symbol] if args.symbol else None
        models = [args.model] if args.model else None
        results = retrain_all(symbols, models)
        print_summary(results)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
