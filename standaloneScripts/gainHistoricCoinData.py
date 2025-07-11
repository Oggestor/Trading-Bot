import os
import sys
import requests
import time
from datetime import datetime, timedelta
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db

def fetch_and_store_one_month_data():
    try:
        # Define the time range for the past month
        end_date = datetime.utcnow()  # Current date and time in UTC
        start_date = end_date - timedelta(days=30)  # Go back one month

        # API setup
        base_url = "https://api.binance.com/api/v3/klines"  # Endpoint for historical data
        coins = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"]

        for coin in coins:
            current_time = end_date

            while current_time > start_date:
                # Calculate timestamps for the request
                start_timestamp = int((current_time - timedelta(minutes=1000)).timestamp() * 1000)
                end_timestamp = int(current_time.timestamp() * 1000)

                params = {
                    "symbol": coin,
                    "interval": "1m",  # 1-minute interval
                    "startTime": start_timestamp,
                    "endTime": end_timestamp,
                    "limit": 1000  # Fetch 1000 minutes of data at a time
                }

                try:
                    response = requests.get(base_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    if not data:
                        break  # No more data available for this range

                    # Insert the data into MongoDB
                    for candle in data:
                        timestamp = datetime.fromtimestamp(candle[0] / 1000)  # Convert from milliseconds
                        data_to_insert = {
                            "stock": coin,
                            "price": candle[4],  # Closing price
                            "timestamp" : datetime.now()
                        }
                        db.insertData(data_to_insert, coin, "coins")

                    # Move to the next batch of 1000 minutes (earlier in time)
                    current_time -= timedelta(minutes=1000)
                    time.sleep(1)  # Respect API rate limits

                except requests.RequestException as e:
                    print(f"API request failed: {e}")
                    time.sleep(5)  # Wait before retrying

        print("One month worth of historical data retrieval and insertion completed.")
        
        # Remove any potential duplicates after data insertion
        db.remove_duplicates("coins")

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)

if __name__ == "__main__":
    fetch_and_store_one_month_data()
