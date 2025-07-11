import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import accountManager as am
from pythonScripts import TradingBot as tb

collections = ['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'DOTUSDC', 'AVAXUSDC', 'LINKUSDC', 'LTCUSDC', 'XRPUSDC', 'SOLUSDC']

# User selection for identity
users = {
    1: 'oskar',
    2: 'william',
    3: 'oskar_test',
    4: 'william_test',
    5: 'oskar_main'
}

print("Who are you?")
for key, value in users.items():
    print(f"{key}: {value}")

try:
    choice = int(input("Enter your choice (1-5): "))
    if choice in users:
        user = users[choice]
        print(f"Selected user: {user}")
    else:
        print("Invalid choice. Please select a number between 1 and 5.")
except ValueError:
    print("Invalid input. Please enter a number between 1 and 5.")

# Define the required columns
required_columns = ['symbol', 'id', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'time', 'isBuyer']

# Initialize an empty DataFrame to store all data
#all_data = pd.DataFrame()
# Try to create the file name
file_name = f'{user}_binance_history.xlsx'
# Check if the file already exists
if not os.path.exists(file_name):
    # If the file does not exist, create an empty DataFrame and save it as a new Excel file
    pd.DataFrame().to_excel(file_name)
    print(f"Created a new Excel file: {file_name}")
    
df = pd.DataFrame()

with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
    for collection in collections:
        data = pd.DataFrame(tb.get_history(user, collection))
        
        # Check if all required columns are present in the DataFrame
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            continue  # Skip this collection if columns are missing
        
        # Filter and clean data
        mod = data.loc[:, required_columns]
        numeric_columns = ["price", "qty", "quoteQty", "commission"]
        mod[numeric_columns] = mod[numeric_columns].apply(pd.to_numeric, errors='coerce')  # Handle any non-numeric values
        
        # Modify 'isBuyer' column: True -> 'buy', False -> 'sell'
        mod['isBuyer'] = mod['isBuyer'].replace({True: 'buy', False: 'sell'})
        
        # Convert 'time' column (UNIX timestamp in milliseconds) to readable datetime format
        mod['time'] = pd.to_datetime(mod['time'], unit='ms')
    
        mod.to_excel(writer, sheet_name=f'{collection}_trade_history', index=False)

        # coded for tax year 2024
        mod = mod.loc[mod['time'] > datetime(2023, 1, 1), :]
        mod = mod.loc[mod['time'] < datetime(2025, 1, 1), :]
        # if both are its great otherwise we need to extract the last and first action until we are on sell/buy
        # check if first is buy, this needs to step up until it finds a buy

        # check if last is sell
        if mod.iloc[0,8] == 'buy':
            mod = mod.iloc[0:,:]

        if mod.iloc[-1,8] == 'sell':
            mod = mod.iloc[:-1,:]
            
        # check if first is buy
        # buy
        buy = sum(mod.loc[mod['isBuyer'] == 'buy', 'quoteQty'])
        # sell
        sell = sum(mod.loc[mod['isBuyer'] == 'sell', 'quoteQty'])
        result = sell - buy
        
        new_row ={
            'Collection': collection,
            'SumBuy': buy,
            'SumSell': sell,
            'Result': result}
            
        # Append row to the dataframe
        df_new = pd.DataFrame(new_row, index=[0])
        df = pd.concat([df, df_new], ignore_index=True)
        
    new_row ={
            'Collection': 'Total',
            'SumBuy': df['SumBuy'].sum(),
            'SumSell': df['SumSell'].sum(),
            'Result': df['Result'].sum()}
    df_new = pd.DataFrame(new_row, index=[0])
    df = pd.concat([df, df_new], ignore_index=True)
        
    df.to_excel(writer, sheet_name=f'results_2024', index=False)