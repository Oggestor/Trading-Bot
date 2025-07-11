import os
import sys
import TradingBot as tb
import numpy as np
from datetime import datetime
import pandas as pd
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from managers import accountManager as am

def evaluate_candidate(collection, TradeResult, user, amount, stratergy=2):
    # Fetch data from the database
    price = tb.live_price(collection)
       
    if stratergy == 1:
        
        list_of_coins = ['BTCUSDC', 'ETHUSDC']
        ARIMA30M = db.getData('predARIMA' + collection + '30M', 'predictions')
        LSTM30M = db.getData('predLSTM' + collection + '30M', 'predictions')
        ARIMA4H = db.getData('predARIMA' + collection + '4H', 'predictions')
        LSTM4H = db.getData('predLSTM' + collection + '4H', 'predictions')
        ARIMA8H = db.getData('predARIMA' + collection + '8H', 'predictions')
        LSTM8H = db.getData('predLSTM' + collection + '8H', 'predictions')
        ARIMA12H = db.getData('predARIMA' + collection + '12H', 'predictions')
        LSTM12H = db.getData('predLSTM' + collection + '12H', 'predictions')
        ARIMA24H = db.getData('predARIMA' + collection + '24H', 'predictions')
        LSTM24H = db.getData('predLSTM' + collection + '24H', 'predictions')
        # Convert price and predicted_price to numeric, coercing errors to NaN
        convert_to_float(ARIMA30M, 'predicted_price')
        convert_to_float(ARIMA4H, 'predicted_price')
        convert_to_float(ARIMA8H, 'predicted_price')
        convert_to_float(ARIMA12H, 'predicted_price')
        convert_to_float(ARIMA24H, 'predicted_price')
        convert_to_float(LSTM30M, 'predicted_price')
        convert_to_float(LSTM4H, 'predicted_price')
        convert_to_float(LSTM8H, 'predicted_price')
        convert_to_float(LSTM12H, 'predicted_price')
        convert_to_float(LSTM24H, 'predicted_price')
        
        if (TradeResult and
            collection in list_of_coins and
            tb.get_specific_balance(user, 'USDC') > amount and 
            TradeResult['bot_action'] != 'BUY' and
            price > ARIMA30M[-1]['predicted_price'] and
            price < LSTM30M[-1]['predicted_price'] and
            price < ARIMA4H[-1]['predicted_price'] and
            price < LSTM4H[-1]['predicted_price'] and
            price < ARIMA8H[-1]['predicted_price'] and
            price < LSTM8H[-1]['predicted_price'] and
            price > ARIMA12H[-1]['predicted_price'] and
            price < LSTM12H[-1]['predicted_price'] and
            price > ARIMA24H[-1]['predicted_price'] and
            price < LSTM24H[-1]['predicted_price']):
            return 'BUY', price
        
        elif (TradeResult and 
            collection not in list_of_coins and
            tb.get_specific_balance(user, 'USDC') > amount and 
            TradeResult['bot_action'] != 'BUY' and
            price > ARIMA30M[-1]['predicted_price'] and
            price < LSTM30M[-1]['predicted_price'] and
            price < ARIMA4H[-1]['predicted_price'] and
            price < LSTM4H[-1]['predicted_price'] and
            price < ARIMA8H[-1]['predicted_price'] and
            price < LSTM8H[-1]['predicted_price'] and
            price > ARIMA12H[-1]['predicted_price'] and
            price < LSTM12H[-1]['predicted_price'] and
            price > ARIMA24H[-1]['predicted_price'] and
            price < LSTM24H[-1]['predicted_price']):
            return 'BUY', price

        # Check if sell conditions are met
        elif (TradeResult and
            TradeResult['bot_action'] == 'BUY' and
            collection in list_of_coins and
            price > ARIMA30M[-1]['predicted_price'] and
            price > LSTM30M[-1]['predicted_price'] and
            price > ARIMA4H[-1]['predicted_price'] and
            price > LSTM4H[-1]['predicted_price'] and
            price > ARIMA8H[-1]['predicted_price'] and
            price > LSTM8H[-1]['predicted_price'] and
            price > ARIMA12H[-1]['predicted_price'] and
            price > LSTM12H[-1]['predicted_price'] and
            price > ARIMA24H[-1]['predicted_price'] and
            price > LSTM24H[-1]['predicted_price']):
            return 'SELL', price
        
        elif (TradeResult and
            TradeResult['bot_action'] == 'BUY' and
            collection not in list_of_coins and
            price < ARIMA30M[-1]['predicted_price'] and
            price > LSTM30M[-1]['predicted_price'] and
            price > ARIMA4H[-1]['predicted_price'] and
            price > LSTM4H[-1]['predicted_price'] and
            price > ARIMA8H[-1]['predicted_price'] and
            price > LSTM8H[-1]['predicted_price'] and      
            price > ARIMA12H[-1]['predicted_price'] and
            price > LSTM12H[-1]['predicted_price'] and
            price > ARIMA24H[-1]['predicted_price'] and
            price > LSTM24H[-1]['predicted_price']):
            return 'SELL', price

        else:
            return 'HOLD', price
    
    elif stratergy == 2:

	#CENSORD

    
def convert_to_float(data, key):
        for item in data:
            try:
                item[key] = float(item[key])
            except (ValueError, TypeError):
                item[key] = None  

def bot_actions():
    collections = ['BTCUSDC']
    users = ['oskar', 'william', 'william_test', 'oskar_test']

    # Loop through all collections and log buy/sell actions in respective collections
    for collection in collections:
        for user in users:
            TradeResult = tb.get_last_action(user, collection)
            print(f"TradeResult: {TradeResult}")
            amount = am.getAmount(user)
            # Evaluate the candidate (buy/sell decision)
            action, price = evaluate_candidate(collection, TradeResult, user, amount)
            if action == 'BUY' and collection in am.getUserCoins(user):
                tb.buy(user, collection, amount)
            elif action == 'SELL':
                tb.sell(user, collection, price)                
    return

if __name__ == '__main__':
    bot_actions()
