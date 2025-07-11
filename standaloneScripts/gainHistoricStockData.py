import os
import sys
import yfinance as yf
from datetime import datetime, timedelta
import pytz  # Add this import for timezone handling
import time
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from pythonScripts import Logger  # Assuming Logger is defined in managers

# Define the ticker symbols for the financial instruments
tickers = {
    'S&P 500 ETF': 'SPY',
    'Dow Jones ETF': 'DIA',
    'NASDAQ-100 ETF': 'QQQ',
    'OMX30': '^OMX',
    'Gold ETF': 'GLD',
    'Silver ETF': 'SLV',
    'EUR/SEK': 'EURSEK=X',
    'EUR/USD': 'EURUSD=X'
}

def fetch_and_store_six_months_data():
    try:
        # Find the last Friday
        today = datetime.utcnow()
        last_friday = today - timedelta(days=(today.weekday() + 3) % 7 + 1)
        
        # Define the time range for the past six months from last Friday
        end_date = last_friday
        start_date = end_date - timedelta(days=30)  # Go back six months

        # Define US stock exchange hours including pre-market and after-market
        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        pre_market_open = now.replace(hour=4, minute=0, second=0, microsecond=0)
        after_market_close = now.replace(hour=20, minute=0, second=0, microsecond=0)

        if pre_market_open <= now <= after_market_close:
            for key, value in tickers.items():
                current_time = end_date

                while current_time > start_date:
                    # Skip weekends
                    if current_time.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                        current_time -= timedelta(days=1)
                        continue

                    # Calculate timestamps for the request
                    start_timestamp = current_time - timedelta(minutes=1000)
                    end_timestamp = current_time

                    try:
                        # Fetch historical data for the past six months with 1-minute interval
                        ticker_data = yf.Ticker(value).history(start=start_timestamp, end=end_timestamp, interval="1m")
                        if not ticker_data.empty:
                            for index, row in ticker_data.iterrows():
                                data_to_insert = {
                                    "stock": key,
                                    "price": row['Close'],
                                    "timestamp": index
                                }
                                db.insertData(data_to_insert, key, "stocks")
                        else:
                            Logger.log(f"No historical data found for {key} ({value})", "WARNING")
                    except Exception as e:
                        Logger.log(f"Error fetching historical data for {key} ({value}): {e}", "ERROR")

                    current_time -= timedelta(minutes=1000)  # Move to the next batch of data
                    time.sleep(1)  # Respect API rate limits
        else:
            Logger.log("Outside US stock exchange hours including pre-market and after-market", "INFO")
    except Exception as e:
        Logger.log(f"An error occurred: {e}", "ERROR")

if __name__ == "__main__":
    fetch_and_store_six_months_data()