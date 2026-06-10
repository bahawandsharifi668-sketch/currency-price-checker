import requests
import json
import os
from datetime import datetime
import numpy as np

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

def predict_future_price(currency1, currency2, days_ahead=1):
    """
    Predict future exchange rate using Linear Regression
    Uses historical data to predict price for days_ahead
    
    Returns: dictionary with prediction details or None
    """
    try:
        historical = get_historical_data(days=30)
        
        if not historical or len(historical) < 3:
            print("Not enough data for prediction (need at least 3 entries)")
            return None
        
        # Prepare data
        timestamps = []
        rates = []
        
        for timestamp, prices in sorted(historical.items()):
            if currency1 in prices and currency2 in prices and prices[currency1] and prices[currency2]:
                try:
                    timestamps.append(timestamp)
                    rate = prices[currency1] / prices[currency2]
                    rates.append(rate)
                except:
                    continue
        
        if len(rates) < 3:
            print("Not enough valid data for prediction (need at least 3 valid entries)")
            return None
        
        # Convert to numpy arrays
        x = np.arange(len(rates))  # Days index: [0, 1, 2, 3, ...]
        y = np.array(rates)  # Exchange rates
        
        # Linear regression (y = mx + b)
        # Calculate slope and intercept using least squares method
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        denominator = (n * sum_x2 - sum_x * sum_x)
        if denominator == 0:
            return None
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict for days_ahead
        next_day_index = len(rates) + days_ahead - 1
        predicted_rate = slope * next_day_index + intercept
        
        # Calculate confidence (R-squared value)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Ensure R-squared is between 0 and 1
        r_squared = max(0, min(1, r_squared))
        confidence = int(r_squared * 100)
        
        # Determine trend
        current_rate = rates[-1]
        if predicted_rate > current_rate * 1.01:  # More than 1% increase
            trend = "📈 صعودی (بالا می‌رود)"
        elif predicted_rate < current_rate * 0.99:  # More than 1% decrease
            trend = "📉 نزولی (پایین می‌رود)"
        else:
            trend = "➡️ ثابت (بدون تغییر)"
        
        # Calculate percentage change
        percentage_change = ((predicted_rate - current_rate) / current_rate) * 100
        
        print(f"\n{'='*50}")
        print(f"Prediction: {currency1}/{currency2}")
        print(f"Current: {current_rate:.6f}")
        print(f"Predicted: {predicted_rate:.6f}")
        print(f"Change: {percentage_change:+.2f}%")
        print(f"Trend: {trend}")
        print(f"Confidence: {confidence}%")
        print(f"Data Points: {len(rates)}")
        print(f"{'='*50}\n")
        
        return {
            'predicted_rate': predicted_rate,
            'current_rate': current_rate,
            'percentage_change': percentage_change,
            'confidence': confidence,
            'trend': trend,
            'data_points': len(rates)
        }
    
    except Exception as e:
        print(f"Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        return None
