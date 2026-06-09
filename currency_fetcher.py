import requests
import json
import os
from datetime import datetime

# Free API endpoint (no key needed)
API_URL = "https://api.exchangerate-api.com/v4/latest/"

# Database file to store prices
DB_FILE = "currency_data.json"

def fetch_current_prices(currencies):
    """
    Fetch real-time prices from API
    currencies: list like ['USD', 'EUR', 'AFN', 'TJS', 'TRY']
    """
    try:
        print(f"Fetching prices from API...")
        # We'll use USD as base and get rates for other currencies
        response = requests.get(API_URL + "USD", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        rates = data['rates']
        
        # Create price dict for requested currencies
        prices = {}
        for currency in currencies:
            if currency == 'USD':
                prices['USD'] = 1.0
            elif currency in rates:
                prices[currency] = rates[currency]
            else:
                prices[currency] = None
        
        print(f"Prices fetched successfully: {prices}")
        return prices
    
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return None

def save_price_data(prices):
    """
    Save prices to JSON database with timestamp
    """
    try:
        # Load existing data
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Add new entry with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data[timestamp] = prices
        
        # Save back
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved: {timestamp}")
        return True
    
    except Exception as e:
        print(f"Error saving data: {e}")
        return False

def get_historical_data(days=30):
    """
    Get last 30 days of data from database
    """
    try:
        if not os.path.exists(DB_FILE):
            print(f"Database file not found: {DB_FILE}")
            return {}
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return {}
        
        # Get only last entries (roughly 30 days)
        sorted_data = sorted(data.items())
        result = dict(sorted_data[-days:] if len(sorted_data) > days else sorted_data)
        
        print(f"Retrieved {len(result)} historical entries")
        return result
    
    except Exception as e:
        print(f"Error reading historical data: {e}")
        return {}

def get_price_change(currency1, currency2, hours=24):
    """
    Calculate price change between two currencies
    """
    try:
        if not os.path.exists(DB_FILE):
            return None, None
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            return None, None
        
        # Get latest and oldest prices
        sorted_data = sorted(data.items())
        latest_prices = sorted_data[-1][1]
        
        # Try to find data from ~24 hours ago
        old_prices = None
        for timestamp, prices in reversed(sorted_data[:-1]):
            old_prices = prices
            break
        
        if not old_prices:
            old_prices = sorted_data[0][1]
        
        # Calculate exchange rate change
        if currency1 in latest_prices and currency2 in latest_prices:
            if latest_prices[currency1] is not None and latest_prices[currency2] is not None:
                if old_prices[currency1] is not None and old_prices[currency2] is not None:
                    latest_rate = latest_prices[currency1] / latest_prices[currency2]
                    old_rate = old_prices[currency1] / old_prices[currency2]
                    
                    if old_rate != 0:
                        change = ((latest_rate - old_rate) / old_rate) * 100
                        return latest_rate, change
        
        return None, None
    
    except Exception as e:
        print(f"Error calculating change: {e}")
        return None, None
