import os
import sys
import requests
import time
import Logger
from datetime import datetime
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db

def real_time_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price")
        data = response.json() 
        for item in data:
            coins = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"]
            for coin in coins:
                if item['symbol'] == coin:
                    price = item['price']
                    data = {
                        "stock" : coin,
                        "price" : price,
                        "timestamp" : datetime.now().replace(second=0, microsecond=0)
                        }
                    db.insertData(data, coin, "coins")
    except requests.RequestException as e:
        Logger.log(f"Request failed: {e}", "ERROR")
        time.sleep(5)
    except Exception as e:
        Logger.log(f"An error occurred: {e}", "ERROR")
        time.sleep(5)

if __name__ == "__main__":
    real_time_price()