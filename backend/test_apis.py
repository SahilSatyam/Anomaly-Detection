import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test all API endpoints"""
    
    print("\n=== Testing API Endpoints ===\n")
    
    # Test 1: Get Stocks List
    print("1. Testing /api/stocks endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/stocks")
        if response.status_code == 200:
            stocks = response.json()
            print("✓ Success! Found stocks:")
            for stock in stocks.get('data', []):
                print(f"  - {stock['symbol']}: {stock['company_name']}")
        else:
            print(f"✗ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Get Stock Data
    print("2. Testing /api/stock-data endpoint...")
    try:
        # Use the first stock from the previous response
        stock_symbol = "AAPL"  # Default to AAPL if no stocks found
        if 'stocks' in locals() and stocks.get('data'):
            stock_symbol = stocks['data'][0]['symbol']
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            'symbol': stock_symbol,
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        response = requests.get(f"{BASE_URL}/api/stock-data", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got stock data for {stock_symbol}")
            print(f"  Found {len(data.get('data', []))} records")
            if data.get('data'):
                print("  Sample data point:")
                print(json.dumps(data['data'][0], indent=2))
        else:
            print(f"✗ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Get Anomalies
    print("3. Testing /api/anomalies endpoint...")
    try:
        params = {
            'symbol': stock_symbol,
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        response = requests.get(f"{BASE_URL}/api/anomalies", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got anomalies for {stock_symbol}")
            print(f"  Found {len(data.get('data', []))} anomalies")
            if data.get('data'):
                print("  Sample anomaly:")
                print(json.dumps(data['data'][0], indent=2))
        else:
            print(f"✗ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Get Settings
    print("4. Testing /api/settings endpoints...")
    try:
        # Test GET settings
        response = requests.get(f"{BASE_URL}/api/settings")
        if response.status_code == 200:
            print("✓ Success! GET /api/settings")
            print("  Current settings:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"✗ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test POST settings
        test_settings = {
            "anomalyThreshold": 0.9,
            "lookbackPeriod": 45,
            "updateFrequency": "hourly"
        }
        
        response = requests.post(f"{BASE_URL}/api/settings", json=test_settings)
        if response.status_code == 200:
            print("✓ Success! POST /api/settings")
            print("  Updated settings:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"✗ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    try:
        # First, make sure requests is installed
        import importlib
        if importlib.util.find_spec("requests") is None:
            print("Installing required package: requests")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            print("requests installed successfully")
        
        test_api_endpoints()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure:")
        print("1. The FastAPI server is running (uvicorn main:app --reload)")
        print("2. You have installed all required packages:")
        print("   pip install requests") 