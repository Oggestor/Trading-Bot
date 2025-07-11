import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from managers import accountManager as am
from pythonScripts import TradingBot as tb

# Collections and user profiles
collections = ['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'DOTUSDC', 'AVAXUSDC', 'LINKUSDC', 'LTCUSDC', 'XRPUSDC', 'SOLUSDC']
users = {
    1: 'oskar',
    2: 'william',
    3: 'oskar_test',
    4: 'william_test',
    5: 'oskar_main'
}

# Menu loop
while True:
    print("Who are you?")
    for key, value in users.items():
        print(f"{key}: {value}")

    try:
        choice = int(input(f"Enter your choice ({', '.join(map(str, users.keys()))}): "))
        user = users.get(choice)
        if user is None:
            print(f"Invalid choice. Please select a valid option: {', '.join(map(str, users.keys()))}.")
            continue
    except ValueError:
        print(f"Invalid input. Please enter a number from {', '.join(map(str, users.keys()))}.")
        continue

    # Begin processing for the selected user
    print(f"\nProfit information for user: {user}")
    header = f"|{'COIN':<10}|{'PROFIT':<15}|{'FEES':<15}|"
    print(header)
    print("-" * len(header))  # Separator line

    prices = []
    for collection in collections:
        data = pd.DataFrame(tb.get_history(user, collection))

        # Define the required columns
        required_columns = ['symbol', 'id', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'time', 'isBuyer']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            continue  # Skip this collection if columns are missing

        # Filter and clean data
        mod = data.loc[:, required_columns]
        numeric_columns = ["price", "qty", "quoteQty", "commission"]
        mod[numeric_columns] = mod[numeric_columns].apply(pd.to_numeric, errors='coerce')  # Handle any non-numeric values

        # Calculate total buy and sell amounts
        total_buy_usdc = mod[mod['isBuyer']]['quoteQty'].sum()
        total_buy_usdc_fee = (mod[mod['isBuyer']]['price'] * mod[mod['isBuyer']]['commission']).sum()
        total_sell_usdc = mod[~mod['isBuyer']]['quoteQty'].sum()
        total_sell_usdc_fee = mod[~mod['isBuyer']]['commission'].sum()

        total_usdc_fee = total_buy_usdc_fee + total_sell_usdc_fee
        profit = total_sell_usdc - total_buy_usdc - total_usdc_fee

        # Identify the last sell transaction
        sells = mod[~mod['isBuyer']]  # Filter sells
        if not sells.empty:
            last_sell_time = sells.iloc[-1]['time']  # Get the time of the last sell

            # Get all buys that happened after the last sell transaction
            buys_after_last_sell = mod[(mod['isBuyer']) & (mod['time'] > last_sell_time)]
            
            # If there are buys after the last sell, exclude those buys
            if not buys_after_last_sell.empty:
                buys_after_last_sell_cost = buys_after_last_sell['quoteQty'].sum()  # Sum of all buys after the last sell
                total_buy_usdc -= buys_after_last_sell_cost  # Subtract the cost of buys after last sell

        # Recalculate profit excluding buys after the last sell
        profit = total_sell_usdc - total_buy_usdc

        print(f"|{collection:<10}|{profit:<15.2f}|{total_usdc_fee:<15.2f}|")
        prices.append(profit)

    print("-" * len(header))  # Separator line
    print(f"Overall the profit for {user} is {np.array(prices).sum():.2f}\n")

    # Ask if the user wants to exit or process another account
    again = input("Do you want to check another user? (y/n): ").strip().lower()
    if again != 'y':
        print("Exiting program. Goodbye!")
        break
