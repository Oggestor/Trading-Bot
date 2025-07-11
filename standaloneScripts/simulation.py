import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
def mergeData(collection):
    """
    Merge the main data with all prediction data for the given collection.
    Args:
        collection (_type_): _description_ This specifies the collection to fetch data from.

    Returns:
        _type_: _description_ This returns the merged data as a pandas dataframe.
    """
    # Fetch the main data
    data = pd.DataFrame(db.getData(collection, "coins"))
    data['timestamp'] = data['timestamp'].dt.round('min')

    # Define prediction intervals and models
    intervals = ["30M", "4H", "8H", "12H", "24H"]
    models = ["ARIMA", "LSTM"]

    # Fetch predictions dynamically and store them in a dictionary
    pred_data = {}
    for interval in intervals:
        for model in models:
            key = f"pred{model}{interval}"
            pred_data[key] = pd.DataFrame(db.getData(f"pred{model}{collection}{interval}", "predictions"))

    # Merge all predictions into `data`
    for key, df in pred_data.items():
        df.rename(columns={'predicted_price': key}, inplace=True)
        data = data.merge(df[['timestamp', key]], on='timestamp', how='left')
    # Fill missing values using forward fill 
    data.ffill(inplace=True)
    data = data.dropna()

    # Convert relevant columns to NumPy arrays for faster access
    columns = ['price', 'predARIMA30M', 'predLSTM30M', 'predARIMA4H', 'predLSTM4H', 
               'predARIMA8H', 'predLSTM8H', 'predARIMA12H', 'predLSTM12H', 'predARIMA24H', 'predLSTM24H', 'timestamp']

    data['price'] = pd.to_numeric(data['price'])
    arrays = [data[col].to_numpy() for col in columns]
    return arrays

def calcProfit(diff, amount, collection):
    if len(diff) == 0:
        print(f'No Sells were perfromed for {collection[:-4]}')
        return
    else:
        diff_value = sum(diff)*amount
        fees = (len(diff)) * 0.001 * amount

    profit = diff_value-fees+amount
    print(f'A start capital of ${amount} has resulted in the following amount ${profit}, for collection {collection[:-4]}')
    print(f'the gain/loss is then ${diff_value-fees} \n')
    return profit


# Will look at a single coin at the time, and matbe just select the best one to trade, first BTCUSDC