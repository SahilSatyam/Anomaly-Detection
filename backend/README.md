# Stock Anomaly Detection - Backend

A Python-based backend service for collecting, analyzing, and serving stock market data with anomaly detection capabilities, focusing on the "Magnificent 7" tech stocks.

## Features

- Automated stock data collection using yfinance
- PostgreSQL database for efficient data storage
- RESTful API endpoints for data access
- Advanced anomaly detection algorithms
- Scheduled data collection and analysis
- Real-time alerts for detected anomalies
- Comprehensive data visualization support

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock_anomaly_detection.git
cd stock_anomaly_detection/backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
```bash
python update_schema.py
```

## Project Structure

```
backend/
├── data_collection/          # Stock data collection modules
│   ├── scheduled_collector.py# Automated data collection
│   └── stock_collector.py    # Stock data fetching logic
├── data_storage/            # Database management
│   ├── database.py         # Database connection and operations
│   └── models.py           # SQLAlchemy models
├── anomaly_detection/      # Anomaly detection algorithms
│   ├── detector.py        # Main detection logic
│   └── algorithms/        # Different detection methods
├── visualization/         # Data visualization helpers
├── alert_system/         # Anomaly alert system
├── main.py              # FastAPI application
└── test_apis.py         # API tests
```

## API Endpoints

### Stock Data
- `GET /api/stocks` - List available stocks
- `GET /api/stocks/{symbol}` - Get stock data for a specific symbol
- `GET /api/stocks/{symbol}/latest` - Get latest stock data

### Anomalies
- `GET /api/anomalies/{symbol}` - Get detected anomalies for a stock
- `GET /api/anomalies/latest` - Get latest detected anomalies
- `POST /api/anomalies/analyze` - Trigger anomaly detection

## Configuration

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/stock_anomaly_db
API_KEY=your_api_key_here
ALERT_EMAIL=your_email@example.com
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Start the scheduled data collector:
```bash
python data_collection/scheduled_collector.py
```

The API will be available at `http://localhost:8000`

## Data Collection

The system automatically collects data for the Magnificent 7 stocks:
- Apple (AAPL)
- Microsoft (MSFT)
- Alphabet (GOOGL)
- Amazon (AMZN)
- NVIDIA (NVDA)
- Meta (META)
- Tesla (TSLA)

Data is collected daily at 9:00 PM IST.

## Anomaly Detection

The system uses multiple algorithms for anomaly detection:
- Statistical methods (Z-score, IQR)
- Machine learning approaches (Isolation Forest)
- Time series analysis (ARIMA, Prophet)

## Testing

Run the test suite:
```bash
pytest test_apis.py
```

## Development

To add sample data for testing:
```bash
python add_sample_data.py
```

To update the database schema:
```bash
python update_schema.py
```

## Monitoring

The application logs are stored in `logs/` directory. Monitor the logs for:
- Data collection status
- Anomaly detection results
- API endpoint access
- Error tracking

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details 