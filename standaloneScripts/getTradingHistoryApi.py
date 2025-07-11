from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pythonScripts import TradingBot as tb
from managers import dbManager as db

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire application

# Define the trading history API endpoint
@app.route('/api/v1/trading-history', methods=['GET'])
def trading_history():
    # Get the user and collection from the query parameters
    user = request.args.get('user')
    collection = request.args.get('collection')

    print(user)
    print(collection)

    history = db.getTradeHistoryData(collection, "coins")

    # Get the actual trades a user has made
    trades = tb.get_history(user, collection)

    print(trades)
    #print(history)

    # Return the trading history as a JSON response
    return jsonify({'message': 'Trading history fetched successfully', 'trades': trades, 'history': history})

if __name__ == '__main__':
    app.run(debug=True)