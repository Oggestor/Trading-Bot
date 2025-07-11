import os
import sys
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from datetime import datetime
from pythonScripts import Logger
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppresses most TF warnings

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
warnings.filterwarnings("ignore")

# Calc durbin watson manual
def CalcDW(residuals):
    numerator = 0
    denominator = 0
    for i in range(1, len(residuals)):
        numerator += (residuals[i] - residuals[i-1])**2
        denominator += residuals[i]**2
        
    dw_stat = numerator/denominator 
    return dw_stat

def AutoArima(collection, interval):
    data = db.queryData(collection, 'coins', interval)
    if (len(data) < 30): 
        return(None)
    dw = []
    aic = []
    order = []
    for p in range(1,3):
        for d in range(1,2):
            for q in range(1,3):
                try:
                    model = ARIMA(data, order=(p, d, q))
                    fitted_model = model.fit()
                    residuals = fitted_model.resid[1:]
                    dw.append(CalcDW(residuals))
                    aic.append(fitted_model.aic)
                    order.append([p,d,q])
                except Exception as e:
                    # Handle any fitting issues
                    Logger.log(f"Model (p={p}, d={d}, q={q}) failed with error: {e}", "ERROR")
                    continue
    
    for i in range(len(aic)):
        if(
            min(aic) == aic[i] and 1.5 < dw[i] < 2.5
            ):
            dw = dw[i]
            best_order = order[i]      
            best_model = ARIMA(data, order=best_order).fit()
    
    forecast = best_model.forecast(steps = 1)
    current_time = datetime.now()

    # Round the minute value to the nearest 00 or 30
    if current_time.minute < 30:
        current_time = current_time.replace(minute=0, second=0, microsecond=0)
    else:
        current_time = current_time.replace(minute=30, second=0, microsecond=0)

    # Format the timestamp
    item = {
            'predicted_price': float(forecast[-1]),
            'timestamp': current_time
            }
    
    db.insertData(item, "predARIMA" + collection + interval, "predictions")

# needs to test this further 
def AutoSarima(collection, interval):
    # Query data from the database
    data = db.queryData(collection, 'coins', interval)
    
    if len(data) < 30: 
        return None
    
    dw, aic, order, seasonal_order = [], [], [], []
    d, D = 1, 1

    for p in range(1, 2):
        for q in range(1, 2):
            for P in range(1, 2):
                for Q in range(1, 2):
                    if int(interval[:-1]) == 24:
                        S = 7
                    elif int(interval[:-1]) == 30:
                        S = 48
                    else:    
                        S = max(1, round(24 / int(interval[:-1]), 0))  # Ensure S >= 1
                    try:
                        model = SARIMAX(data, order=(p, d, q), seasonal_order=(P, D, Q, S))
                        fitted_model = model.fit(disp=False)  # Suppress unnecessary output
                        residuals = fitted_model.resid
                        if len(residuals) > 1:
                            residuals = residuals[1:]
                        dw_value = CalcDW(residuals)
                        dw.append(dw_value)
                        aic.append(fitted_model.aic)
                        order.append([p, d, q])
                        seasonal_order.append([P, D, Q, S])
                    except Exception as e:
                        Logger.log(f"SARIMA Model (p={p}, q={q}, P={P}, Q={Q}, S={S}) failed: {e}", "ERROR")
    
    if not aic:
        Logger.log(f"No valid SARIMA model found for collection: {collection}, interval: {interval}", "ERROR")
        return None

    # Get best model index
    best_idx = np.argmin(aic)
    if not (1.5 < dw[best_idx] < 2.5):
        Logger.log(f"No SARIMA model met DW criteria for {collection}, interval: {interval}", "ERROR")
        return None

    # Fit the best SARIMA model
    best_order = order[best_idx]
    best_seasonal_order = seasonal_order[best_idx]
    best_model = SARIMAX(data, order=best_order, seasonal_order=best_seasonal_order).fit(disp=False)

    # Forecast next step
    forecast = best_model.forecast(steps=1)

    # Round timestamp to nearest 00 or 30 min
    current_time = datetime.now().replace(minute=(datetime.now().minute // 30) * 30, second=0, microsecond=0)

    # Store prediction
    item = {
        'predicted_price': float(forecast[-1]),
        'timestamp': current_time
    }

    db.insertData(item, "predSARIMA" + collection + interval, "predictions")

def AutoLSTM(collection, interval):
    
    data = db.queryData(collection, 'coins', interval)
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data.reshape(-1, 1))

    def create_sequences(data, time_step=1):
        X, y = [], []
        for i in range(len(data) - time_step):
            X.append(data[i:(i + time_step), 0])
            y.append(data[i + time_step, 0])
        return np.array(X), np.array(y)

    time_step = 5
    X, y = create_sequences(data_scaled, time_step)
    X = X.reshape(X.shape[0], X.shape[1], 1)
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    # Build the LSTM model
    model = Sequential()
    model.add(LSTM(units=30, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=30, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)

    y_pred = model.predict(X_test)

    y_pred = scaler.inverse_transform(y_pred)
    y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

    #r2 = r2_score(y_test, y_pred)
    #print(r2)
    
    last_sequence = data_scaled[-time_step:].reshape(1, time_step, 1)
    next_prediction_scaled = model.predict(last_sequence)
    next_prediction = scaler.inverse_transform(next_prediction_scaled)
    
    current_time = datetime.now()

    # Round the minute value to the nearest 00 or 30
    if current_time.minute < 30:
        current_time = current_time.replace(minute=0, second=0, microsecond=0)
    else:
        current_time = current_time.replace(minute=30, second=0, microsecond=0)

    # Format the timestamp
    item = {
            'predicted_price': float(next_prediction[0, 0]),
            'timestamp': current_time 
            }
    
    db.insertData(item, "predLSTM" + collection + interval, "predictions")