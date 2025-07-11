import sys
import os
import numpy as np
import pandas as pd
import random as rand
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from standaloneScripts import simulation as sim
import matplotlib.pyplot as plt

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.preprocessing import StandardScaler  # Import StandardScaler

# Assuming the data is merged properly
collection = 'BTCUSDC'
arrays = sim.mergeData(collection)
# Assuming arrays are loaded as per your description
prices = arrays[0]  # Actual prices
predictions = arrays[1:11]  # ARIMA and LSTM predictions
timestamps = arrays[11]  # Timestamps

# Label creation based on your strategy
lookahead = 60
buy_labels = []
sell_labels = []
in_position = False  # Track if we already "own" after a buy

for i in range(len(prices)):
    future_window = prices[i:i+lookahead]
    current_price = prices[i]

    if len(future_window) < lookahead:
        buy_labels.append(0)
        sell_labels.append(0)
        continue

    if not in_position:
        # Only allow buy if we are NOT in a position
        if current_price == min(future_window):  # Simple logic for buying
            buy_labels.append(1)
            sell_labels.append(0)
            in_position = True
        else:
            buy_labels.append(0)
            sell_labels.append(0)
    else:
        # Only allow sell if we ARE in a position
        if current_price == max(future_window):  # Simple logic for selling
            buy_labels.append(0)
            sell_labels.append(1)
            in_position = False
        else:
            buy_labels.append(0)
            sell_labels.append(0)

# Prepare DataFrame with features
data = pd.DataFrame({
    'actual_price': prices,
    'predARIMA30M': predictions[0],
    'predLSTM30M': predictions[1],
    'predARIMA4H': predictions[2],
    'predLSTM4H': predictions[3],
    'predARIMA8H': predictions[4],
    'predLSTM8H': predictions[5],
    'predARIMA12H': predictions[6],
    'predLSTM12H': predictions[7],
    'predARIMA24H': predictions[8],
    'predLSTM24H': predictions[9],
    'timestamp': pd.to_datetime(timestamps)  # Convert to datetime
})

# Feature engineering - Extract time-based features
data['hour'] = data['timestamp'].dt.hour
data['dayofweek'] = data['timestamp'].dt.dayofweek
data['dayofyear'] = data['timestamp'].dt.dayofyear
data['month'] = data['timestamp'].dt.month

# Drop timestamp as it's no longer needed
data.drop(columns=['timestamp'], inplace=True)

# Combine buy and sell labels into one classification target (binary: buy=1, sell=-1, no-action=0)
labels = [0 if buy_labels[i] == 1 else (1 if sell_labels[i] == 1 else 2) for i in range(len(buy_labels))]

# Add labels to the DataFrame
data['label'] = labels

# Features and target
X = data.drop(columns=['actual_price', 'label'])
y = data['label']

# Train-test split (keeping the time series intact)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# **Standardize the Features**
scaler = StandardScaler()

# Fit and transform on the training data
X_train_scaled = scaler.fit_transform(X_train)

# Transform on the test data using the same scaler (to avoid data leakage)
X_test_scaled = scaler.transform(X_test)

# Undersample the majority class (label == 2) using RandomUnderSampler
undersampler = RandomUnderSampler(sampling_strategy={2: min(y_train.value_counts())}, random_state=42)
X_train_under, y_train_under = undersampler.fit_resample(X_train_scaled, y_train)

# Apply SMOTE to balance the resampled data (resampling minority classes)
smote = SMOTE(sampling_strategy='auto', random_state=42)
X_res, y_res = smote.fit_resample(X_train_under, y_train_under)

# Class weight adjustment for XGBoost
class_weights = {0: 5, 1: 5, 2: 1}  # Adjusting class weights

# Train XGBoost classifier on the balanced data (after both undersampling 
# and SMOTE)
model = xgb.XGBClassifier(objective='multi:softmax', num_class=3, n_estimators=2000, 
                          learning_rate=0.01, max_depth=6, scale_pos_weight=class_weights, class_weight='balanced')
model.fit(X_res, y_res)  # Use resampled data

# Predictions
y_pred = model.predict(X_test_scaled)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy}")
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Optional: Plotting the predictions vs actual labels
plt.figure(figsize=(14, 6))
plt.plot(y_test.values, label='Actual', color='blue')
plt.plot(y_pred, label='Predicted', color='red', linestyle='dashed')
plt.title(f'XGBoost Predictions vs Actual Buy/Sell Signals')
plt.xlabel('Time')
plt.ylabel('Label (Buy=1, Sell=-1, No-Action=0)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
