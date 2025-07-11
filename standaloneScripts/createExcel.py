import sys
import os
import pandas as pd
import numpy as np
from openpyxl import load_workbook
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db

def createExcel(collection):
        data = pd.DataFrame(db.getData(collection, "coins"))
        data['timestamp'] = data['timestamp'].dt.round('min')        
        intervals = ["30M", "4H", "8H", "12H", "24H"]
        models = ["ARIMA", "LSTM"]

        # Fetch predictions dynamically and store them in a dictionary
        pred_data = {}
        for interval in intervals:
                for model in models:
                        key = f"pred{model}{interval}"
                        pred_data[key] = pd.DataFrame(db.getData(f"pred{model}{collection}{interval}", "predictions"))

        for key, df in pred_data.items():
                df.rename(columns={'predicted_price': key}, inplace=True)
                data = data.merge(df[['timestamp', key]], on='timestamp', how='left')
                
        # Fill missing values using forward fill 
        data.ffill(inplace=True)
        data = data.dropna()

        excel_path = f'{collection}.xlsx'
        data[['timestamp', 'price', 'predARIMA30M', 'predLSTM30M', 'predARIMA4H', 'predLSTM4H', 
              'predARIMA8H', 'predLSTM8H', 'predARIMA12H', 'predLSTM12H', 'predARIMA24H', 'predLSTM24H']].to_excel(excel_path, index=False)

if __name__ == "__main__":
    collection = "BTCUSDC"
    createExcel(collection)
    print(f"Excel file created for {collection} at {collection}.xlsx")