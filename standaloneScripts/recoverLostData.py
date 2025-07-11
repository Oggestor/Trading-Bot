import os
import sys
import requests
import logging
from datetime import datetime, timedelta
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db

def truncate_to_minute(dt):
    """Remove seconds and microseconds from a datetime."""
    return dt.replace(second=0, microsecond=0)

def fetch_and_insert_historical_data(symbol, start_time, end_time):
    """Fetch historical minute-level data from Binance and insert it into the database."""
    base_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        'symbol': symbol,
        'interval': '1m',
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000)
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            logger.warning(f"No data returned for {symbol} from {start_time} to {end_time}")
            return
        
        for candle in data:
            timestamp = datetime.fromtimestamp(candle[0] / 1000)
            timestamp = truncate_to_minute(timestamp)
            data_to_insert = {
                "stock": symbol,
                "price": candle[4],  # Closing price
                "timestamp": timestamp
            }

            existing = db.findOne({"stock": symbol, "timestamp": timestamp}, symbol)
            if not existing:
                db.insertData(data_to_insert, symbol, "coins")
                logger.info(f"Inserted {symbol} data at {timestamp}")
            else:
                logger.debug(f"Already exists: {symbol} at {timestamp}")
        
        time.sleep(0.5)  # To respect API rate limits
    
    except requests.RequestException as e:
        logger.error(f"Request failed for {symbol} from {start_time} to {end_time}: {e}")

def find_and_fill_gaps(symbol):
    """Find missing minute intervals and fetch them."""
    existing_data = db.getData(symbol, "coins")
    if not existing_data:
        logger.warning(f"No existing data found for {symbol}.")
        return
    
    # Normalize timestamps
    timestamps = [truncate_to_minute(record['timestamp']) for record in existing_data if 'timestamp' in record]
    if not timestamps:
        logger.warning(f"No valid timestamps for {symbol}.")
        return

    timestamps.sort()
    timestamp_set = set(timestamps)

    start_time = timestamps[0]
    end_time = timestamps[-1]
    current_time = start_time

    missing_minutes = []

    while current_time <= end_time:
        if current_time not in timestamp_set:
            missing_minutes.append(current_time)
        current_time += timedelta(minutes=1)

    logger.info(f"{symbol}: {len(missing_minutes)} missing minutes detected.")

    # Fetch each missing minute individually (you can batch these if needed)
    for missing_time in missing_minutes:
        fetch_and_insert_historical_data(symbol, missing_time, missing_time + timedelta(minutes=1))

    # Deduplicate just in case
    db.remove_duplicates(symbol)

def main():
    symbols = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"]
    for symbol in symbols:
        logger.info(f"Checking gaps for {symbol}...")
        find_and_fill_gaps(symbol)

if __name__ == "__main__":
    main()
