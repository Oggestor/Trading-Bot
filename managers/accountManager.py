import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pythonScripts import Logger

# Path to the JSON file
file_path_1 = "./config/UserConfiguration.json"
file_path_2 = "/home/alan/repo/config/UserConfiguration.json"
file_path = file_path_1 if os.path.exists(file_path_1) else file_path_2

# Load the JSON configuration
try:
    with open(file_path, 'r') as file:
        config = json.load(file)
except Exception as e:
        Logger.log(f"Error reading the config file: {e}", "ERROR")

def getAmount(user):
    if user in config:
        return config[user]['amount']
    else:
        Logger.log(f"Key {user} not found in the configuration file", "ERROR")

def getUseBear(user):
    if user in config:
        return config[user]['bear']
    else:
        Logger.log(f"Key {user} not found in the configuration file", "ERROR")

def getUserCoins(user):
    if user in config:
        return config[user]['coins']
    else:
        Logger.log(f"Key {user} not found in the configuration file", "ERROR")