import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from pythonScripts import TradingBot as tb

def vizData():
    option = input("Choose which plot to show. \n The options are as follow: \n 1. BTC \n 2. ETH \n 3. ADA \n 4. DOT \n 5. AVAX \n 6. LINK \n 7. LTC \n 8. XRP \n 9. SOL \n to exit press q \n")
    if option == "q":
        return "quit"
    try:
        option = int(option) - 1
        if option < 0 or option > 8:
            raise ValueError
        collection = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"][option]
    except ValueError:
        print("Error: Please write a valid number between 1 and 9.")
        return "invalid"
    
    """
    Fetch, process, and plot actual and predicted data for a given collection.

    Parameters:
    - collection: Name of the collection to fetch and plot data from.
    """
    # Fetch data from MongoDB collections
    data = pd.DataFrame(db.getData(collection, "coins"))
    predARIMA30M = pd.DataFrame(db.getData("predARIMA" + collection + "30M", "predictions"))
    predLSTM30M = pd.DataFrame(db.getData("predLSTM" + collection + "30M", "predictions"))
    predARIMA4H = pd.DataFrame(db.getData("predARIMA" + collection + "4H", "predictions"))
    predLSTM4H = pd.DataFrame(db.getData("predLSTM" + collection + "4H", "predictions"))
    predARIMA8H = pd.DataFrame(db.getData("predARIMA" + collection + "8H", "predictions"))
    predLSTM8H = pd.DataFrame(db.getData("predLSTM" + collection + "8H", "predictions"))
    predARIMA12H = pd.DataFrame(db.getData("predARIMA" + collection + "12H", "predictions"))
    predLSTM12H = pd.DataFrame(db.getData("predLSTM" + collection + "12H", "predictions"))
    predARIMA24H = pd.DataFrame(db.getData("predARIMA" + collection + "24H", "predictions"))
    predLSTM24H = pd.DataFrame(db.getData("predLSTM" + collection + "24H", "predictions"))

    # Process the main data
    if not data.empty:
        data['price'] = pd.to_numeric(data['price'], errors='coerce')
        data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
        data.sort_values(by='timestamp', inplace=True)
        data.reset_index(drop=True, inplace=True)

    # proabbaly more like 20min in the future
    # Adjust timestamps for predictions
    def adjust_timestamps(pred_df, interval):
        if not pred_df.empty:
            pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'], errors='coerce')
            if interval == '30M':
                pred_df['timestamp'] = pred_df['timestamp'] + pd.DateOffset(minutes=30)
            elif interval == '4H':
                pred_df['timestamp'] = pred_df['timestamp'] + pd.DateOffset(hours=4)
            elif interval == '8H':
                pred_df['timestamp'] = pred_df['timestamp'] + pd.DateOffset(hours=8)
            elif interval == '12H':
                pred_df['timestamp'] = pred_df['timestamp'] + pd.DateOffset(hours=12)
            elif interval == '24H':
                pred_df['timestamp'] = pred_df['timestamp'] + pd.DateOffset(hours=24)
            pred_df.sort_values(by='timestamp', inplace=True)
            pred_df.reset_index(drop=True, inplace=True)

    # when adjuting like this im ruining the timestamp events
    #adjust_timestamps(predARIMA30M, '30M')
    #adjust_timestamps(predLSTM30M, '30M')
    #adjust_timestamps(predARIMA4H, '4H')
    #adjust_timestamps(predLSTM4H, '4H')
    #adjust_timestamps(predARIMA8H, '8H')
    #adjust_timestamps(predLSTM8H, '8H')
    #adjust_timestamps(predARIMA12H, '12H')
    #adjust_timestamps(predLSTM12H, '12H')
    #adjust_timestamps(predARIMA24H, '24H')
    #adjust_timestamps(predLSTM24H, '24H')

    # Plot actual and predicted prices using Plotly
    fig = go.Figure()

    if not data.empty:
        fig.add_trace(go.Scatter(x=data['timestamp'], y=data['price'], mode='lines', name='Actual Price'))

    if not predARIMA30M.empty:
        fig.add_trace(go.Scatter(x=predARIMA30M['timestamp'], y=predARIMA30M['predicted_price'], mode='lines', name='ARIMA 30M Prediction', line=dict(shape='hv')))

    if not predLSTM30M.empty:
        fig.add_trace(go.Scatter(x=predLSTM30M['timestamp'], y=predLSTM30M['predicted_price'], mode='lines', name='LSTM 30M Prediction', line=dict(shape='hv')))

    if not predARIMA4H.empty:
        fig.add_trace(go.Scatter(x=predARIMA4H['timestamp'], y=predARIMA4H['predicted_price'], mode='lines', name='ARIMA 4H Prediction', line=dict(shape='hv')))

    if not predLSTM4H.empty:
        fig.add_trace(go.Scatter(x=predLSTM4H['timestamp'], y=predLSTM4H['predicted_price'], mode='lines', name='LSTM 4H Prediction', line=dict(shape='hv')))

    if not predARIMA8H.empty:
        fig.add_trace(go.Scatter(x=predARIMA8H['timestamp'], y=predARIMA8H['predicted_price'], mode='lines', name='ARIMA 8H Prediction', line=dict(shape='hv')))

    if not predLSTM8H.empty:
        fig.add_trace(go.Scatter(x=predLSTM8H['timestamp'], y=predLSTM8H['predicted_price'], mode='lines', name='LSTM 8H Prediction', line=dict(shape='hv')))

    if not predARIMA12H.empty:
        fig.add_trace(go.Scatter(x=predARIMA12H['timestamp'], y=predARIMA12H['predicted_price'], mode='lines', name='ARIMA 12H Prediction', line=dict(shape='hv')))

    if not predLSTM12H.empty:
        fig.add_trace(go.Scatter(x=predLSTM12H['timestamp'], y=predLSTM12H['predicted_price'], mode='lines', name='LSTM 12H Prediction', line=dict(shape='hv')))

    if not predARIMA24H.empty:
        fig.add_trace(go.Scatter(x=predARIMA24H['timestamp'], y=predARIMA24H['predicted_price'], mode='lines', name='ARIMA 24H Prediction', line=dict(shape='hv')))

    if not predLSTM24H.empty:
        fig.add_trace(go.Scatter(x=predLSTM24H['timestamp'], y=predLSTM24H['predicted_price'], mode='lines', name='LSTM 24H Prediction', line=dict(shape='hv')))

    fig.update_layout(
        title=f"{collection} Actual vs Predicted Prices",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark"
    )

    fig.show()

if __name__ == '__main__':
    vizData()