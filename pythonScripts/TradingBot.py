from datetime import datetime
from binance import Client
import os
import sys
import dotenv
import math
import decimal
from binance.exceptions import BinanceAPIException
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pythonScripts import Logger
import time

dotenv.load_dotenv()

#A dictionary containing the different account keys
users_credentials = {
    'oskar': {
        'api_key': os.getenv('OSKAR_BINANCE_API_KEY'),
        'api_secret': os.getenv('OSKAR_BINANCE_API_SECRET')
    },
    'william': {
        'api_key': os.getenv('WILLIAM_BINANCE_API_KEY'),
        'api_secret': os.getenv('WILLIAM_BINANCE_API_SECRET')
    },
    'oskar_test':{
        'api_key': os.getenv('OSKARTEST_BINANCE_API_KEY'),
        'api_secret': os.getenv('OSKARTEST_BINANCE_API_SECRET')
    },
    'william_test': {
        'api_key': os.getenv('WILLIAMTEST_BINANCE_API_KEY'),
        'api_secret': os.getenv('WILLIAMTEST_BINANCE_API_SECRET')
    },
    'oskar_main':{
        'api_key': os.getenv('OSKARMAIN_BINANCE_API_KEY'),
        'api_secret': os.getenv('OSKARMAIN_BINANCE_API_KEY_SECRET')
    }
}

def get_client(user):
    if user in users_credentials:
        api_key = users_credentials[user]['api_key']
        api_secret = users_credentials[user]['api_secret']
        return Client(api_key, api_secret)
    else:
        Logger.log(f"No credentials found for user {user}", "ERROR")

def get_specific_balance(user, asset):
    client = get_client(user)
    try:
        balance = client.get_asset_balance(asset=asset)
    except BinanceAPIException as e:
        Logger.log(f"Error with binance API {e}", "ERROR")
    return float(balance['free'])

def get_lot_size_info(user, symbol):
    client = get_client(user)
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    step_size = float(f['stepSize'])
                    precision = int(abs(decimal.Decimal(f['stepSize']).as_tuple().exponent))
                    return min_qty, step_size, precision
    return None, None, None

def buy(user, collection, invest_amount):
    client = get_client(user)

    try:
        # Create the buy order
        order = client.create_order(
            symbol=collection,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quoteOrderQty=invest_amount
        )
        Logger.log(f"Order placed {order} for {user} with amount {invest_amount}", "INFO")

        # Get the order ID and status
        order_id = order['orderId']
        order_status = None
        while order_status != 'FILLED':
            order_details = client.get_order(symbol=collection, orderId=order_id)
            order_status = order_details['status']

            Logger.log(f"Order status {order_status} for {user}", "INFO")

    except BinanceAPIException as e:
        Logger.log(f"API error occurred {e.message} for user {user}", "ERROR")

    except Exception as e:
        Logger.log(f"An unexpected error occurred: {str(e)}", "ERROR")
        
def sell(user, collection, price):
    client = get_client(user)
    available_balance = get_specific_balance(user, collection[:-4])
    min_qty, step_size, precision = get_lot_size_info(user, collection)

    if available_balance > min_qty and 10 < available_balance * price:
        adjusted_balance = available_balance * 0.999
        quantity = math.floor(adjusted_balance / step_size) * step_size
        quantity = round(quantity, precision)

        if quantity >= min_qty:
            order = client.create_order(
                symbol=collection,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            Logger.log(f"Order placed {order} for {user} with amount {quantity}", "INFO")
        else:
            Logger.log(f"Adjusted quantity {quantity} is less than minimum order size {min_qty} for user {user}", "INFO")
    else:
        Logger.log(f"Insufficient {collection} balance for user {user}", "INFO")
        return
    
def get_last_action(user, collection):
    try:
        last_trade_list = get_client(user).get_my_trades(symbol=collection, limit=1)  # Returns a list of trades

        # covers the case where it gets the trading history but it is empty for the user
        # and this coin.
        if len(last_trade_list) > 0:
            last_trade = last_trade_list[0]  # Get the first (most recent) trade
            # Check if the user was a buyer or seller, and create the TradeResult dictionary
            if last_trade['isBuyer'] == True:  # Assuming 'isBuyer' is a key in the trade dictionary
                TradeResult = {'price': float(last_trade['price']), 'bot_action': 'BUY'}
            else:
                TradeResult = {'price': float(last_trade['price']), 'bot_action': 'SELL'}
        else:
            TradeResult = {'bot_action': 'No trades'}

        # Just spams the log with last actions
        #Logger.log(f"Last action for user {user} in collection {collection}: {TradeResult}", "INFO")
        return TradeResult

    except Exception as e:
        Logger.log(f"Cannot find last trade action for {user} in collection {collection}: {e}", "ERROR")
        return {'bot_action': 'No trades'}

#def get_history(user, collection):
#    last_trade_list = get_client(user).get_my_trades(symbol=collection)  # Returns a list of trades
#    return last_trade_list

def get_history(user, symbol):
    all_trades = []
    limit = 1000  # Adjust the limit as necessary

    # Initial variables
    from_id = None  # To store the ID of the last trade to continue pagination

    while True:
        try:
            # Get trades in batches (paginate if needed)
            trades = get_client(user).get_my_trades(symbol=symbol, limit=limit, fromId=from_id)
            if not trades:
                break  # Exit if no more trades are available

            all_trades.extend(trades)
            from_id = trades[-1]['id'] + 1  # Set fromId for next batch
            
            # Sleep to avoid hitting API limits
            time.sleep(1)

        except Exception as e:
            print(f"Error fetching trades: {e}")
            break

    return all_trades
   
def live_price(collection):
    response = requests.get("https://api.binance.com/api/v3/ticker/price")
    data = response.json() 
    for item in data:
        coins = [collection]
        for coin in coins:
            if item['symbol'] == coin:
                price = item['price']
    
    return(float(price))
