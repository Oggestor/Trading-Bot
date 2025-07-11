import os
import sys
import yfinance as yf
import time
from datetime import datetime
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from pythonScripts import Logger

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

def fetch_ticker_data(ticker):
    """Fetch real-time data for a given ticker."""
    try:
        ticker_data = yf.Ticker(ticker).history(period="1d", interval="1m")
        if not ticker_data.empty:
            return ticker_data['Close'].iloc[-1]
        else:
            Logger.log(f"No data found for ticker {ticker}", "WARNING")
            return None
    except Exception as e:
        Logger.log(f"Error fetching data for ticker {ticker}: {e}", "ERROR")
        return None

def insert_data_to_db(data):
    """Insert fetched data into the database."""
    for key, value in data.items():
        if value is not None:
            data_to_insert = {
                "stock": key,
                "price": value,
                "timestamp" : datetime.now()
            }
            db.insertData(data_to_insert, key, "stocks")
        else:
            Logger.log(f'{key}: Data unavailable', "INFO")

def fetch_real_time_prices():
    """Fetch real-time prices for defined tickers and insert into the database."""
    try:
        data = {}
        for key, value in tickers.items():
            data[key] = fetch_ticker_data(value)
        
        insert_data_to_db(data)
    except Exception as e:
        Logger.log(f"An error occurred: {e}", "ERROR")
        time.sleep(5)

if __name__ == "__main__":
    fetch_real_time_prices()
