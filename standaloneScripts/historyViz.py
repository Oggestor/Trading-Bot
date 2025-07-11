import os
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pythonScripts import TradingBot as tb
from managers import dbManager as db

# Fetching bot history
def botHistory(user, collection):
    data = pd.DataFrame(tb.get_history(user, collection))
    required_columns = ['symbol', 'id', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'time', 'isBuyer']

    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        return

    mod = data.loc[:, required_columns]
    numeric_columns = ["price", "qty", "quoteQty", "commission"]
    mod[numeric_columns] = mod[numeric_columns].apply(pd.to_numeric, errors='coerce')

    mod['isBuyer'] = mod['isBuyer'].replace({True: 'buy', False: 'sell'})

    mod['time'] = pd.to_datetime(mod['time'], unit='ms')
    return mod[['price', 'time', 'isBuyer']]

# Function to visualize data with plotly
def vizData():
    option_user = input("Choose which user to use \n 1. oskar \n 2. william \n 3. william_test \n 4. oskar_test \n 5. oskar_main \n to exit press q \n")
    if option_user == "q":
        return "quit"
    try:
        option_user = int(option_user) - 1
        if option_user < 0 or option_user > 4:
            raise ValueError
        user = ['oskar', 'william', 'william_test', 'oskar_test', 'oskar_main'][option_user]
    except ValueError:
        print("Error: Please write a valid number between 1 and 5.")
        return "invalid"
    
    option_coin = input("Choose which plot to show. \n The options are as follow: \n 1. BTC \n 2. ETH \n 3. ADA \n 4. DOT \n 5. AVAX \n 6. LINK \n 7. LTC \n 8. XRP \n 9. SOL \n to exit press q \n")
    if option_coin == "q":
        return "quit"
    try:
        option_coin = int(option_coin) - 1
        if option_coin < 0 or option_coin > 8:
            raise ValueError
        collection = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"][option_coin]
    except ValueError:
        print("Error: Please write a valid number between 1 and 9.")
        return "invalid"

    # Fetch data
    data = pd.DataFrame(db.getData(collection, "coins") or [])
    actions = botHistory(user, collection)

    if not data.empty:
        data['price'] = pd.to_numeric(data['price'], errors='coerce')
        data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce', utc=True)
        data.sort_values(by='timestamp', inplace=True)
        data.reset_index(drop=True, inplace=True)

    if not actions.empty:
        actions['time'] = pd.to_datetime(actions['time'], errors='coerce', utc=True) 

    if not data.empty and not actions.empty:
        start_time = data['timestamp'].min()
        end_time = data['timestamp'].max()
        actions = actions[(actions['time'] >= start_time) & (actions['time'] <= end_time)]

    # Plotting
    fig = make_subplots(rows=1, cols=1)

    if not data.empty:
        fig.add_trace(go.Scatter(x=data['timestamp'], y=data['price'], mode='lines', name='Actual', line=dict(color='#83dfe9')))

    if not actions.empty:
        # one hour off
        actions['time'] += pd.DateOffset(hours=1)
        buy_actions = actions[actions['isBuyer'] == 'buy']
        sell_actions = actions[actions['isBuyer'] == 'sell']
        fig.add_trace(go.Scatter(x=buy_actions['time'], y=buy_actions['price'], mode='markers', name='Buy', marker=dict(color='green', size=10, opacity=0.7)))
        fig.add_trace(go.Scatter(x=sell_actions['time'], y=sell_actions['price'], mode='markers', name='Sell', marker=dict(color='red', size=10, opacity=0.7)))

        # Find the min and max values of the price data
        min_price = data['price'].min()
        max_price = data['price'].max()

        # Add some margin to the y-axis range (e.g., 5% above and below the min/max values)
        y_margin = (max_price - min_price) * 0.1  # Increase margin to avoid tight zooming

        # Optional: Set a minimum and maximum for the y-axis range to avoid extreme scaling
        y_min = min_price - y_margin
        y_max = max_price + y_margin

        # Ensure the y-axis range is not too small
        y_min = max(y_min, min_price * 0.9)  # Ensure a lower bound (10% below min_price)
        y_max = min(y_max, max_price * 1.1)  # Ensure an upper bound (10% above max_price)

        # Set the y-axis range dynamically based on the data
        fig.update_layout(
            yaxis=dict(
                showgrid=True,
                range=[y_min, y_max]  # Adjust the range to fit the data with margin
            ),
            dragmode='pan',
            title=f'Trading history of {collection} for {user}',
            xaxis_title='Timestamp',
            yaxis_title='Price',
            template='plotly_dark',
            autosize=True,
            showlegend=True,
            hovermode='closest'
        )

    # Update the grid style
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='gray')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='gray')

    fig.show()

if __name__ == '__main__':
    while True:
        result = vizData() 
        if result == "quit":
            print("Exiting...")
            break
