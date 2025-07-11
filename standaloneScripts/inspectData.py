import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from openpyxl import load_workbook

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from standaloneScripts import simulation as sim

def inspectData(collection, excel = False, range = 2880):
    # Merging data
    #arrays = sim.mergeData(collection)
    arrays = pd.DataFrame(db.getData(collection, "coins"))
    columns = ['price', 'timestamp']
    arrays['price'] = pd.to_numeric(arrays['price'])
    arrays = [arrays[col].to_numpy() for col in columns]
    
    # Initialize lists to store data
    prices = []
    timestamps = []
    median_list = []
    mean_list = []
    min_list = []
    max_list = []
    std_list = []

    # Iterate through the rows and collect data
    for row in zip(*arrays):
        prices.append(row[0])
        timestamps.append(row[1])  # Assuming the timestamp is at index 5

        if len(prices) > range:

            # Calculate statistics for the window of the last 2880 prices
            median_list.append(np.median(prices[-range:]))
            mean_list.append(np.mean(prices[-range:]))
            min_list.append(np.min(prices[-range:]))
            max_list.append(np.max(prices[-range:]))
            std_list.append(np.std(prices[-range:]))

    # Check if the length of all lists is the same
    min_length = min(len(prices), len(timestamps), len(median_list), len(mean_list), len(min_list), len(max_list), len(std_list))
    if min_length > 0:
        # Trim all lists to the same length
        prices = prices[-min_length:]
        timestamps = timestamps[-min_length:]
        median_list = median_list[-min_length:]
        mean_list = mean_list[-min_length:]
        min_list = min_list[-min_length:]
        max_list = max_list[-min_length:]
        std_list = std_list[-min_length:]

    # Prepare the DataFrame to export
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Price': prices,
        'Median': median_list,
        'Mean': mean_list,
        'Min': min_list,
        'Max': max_list,
        'StdDev': std_list
    })

    if excel:
        # Write the DataFrame to an Excel file
        excel_path = f'{collection}_statistics.xlsx'
        df.to_excel(excel_path, index=False)

        # Load the workbook to modify it
        wb = load_workbook(excel_path)
        ws = wb.active

        # Freeze the top row
        ws.freeze_panes = 'A2'

        # Save the modified workbook
        wb.save(excel_path)

        print(f"Excel file saved as {excel_path}")

    # Create the plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Price'], mode='lines', name='Price', line=dict(shape='hv', color = 'blue')))

    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Median']+2*df['StdDev'], mode='lines', name='Median', line=dict(shape='hv', color = 'darkred')))
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Mean']+2*df['StdDev'], mode='lines', name='Mean', line=dict(shape='hv', color = 'red')))
    
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Median']-3*df['StdDev'], mode='lines', name='Median', line=dict(shape='hv', color = 'darkgreen')))
    fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Mean']-3*df['StdDev'], mode='lines', name='Mean', line=dict(shape='hv', color = 'green')))

    fig.update_layout(
        title=f"{collection} Price Statistics",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark"
    )

    fig.show()

if __name__ == "__main__":
    inspectData(collection = "BTCUSDC", excel = True, range = 1440)
