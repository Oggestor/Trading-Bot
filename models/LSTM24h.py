import os
import sys
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Now you should be able to import from 'models'
from pythonScripts import ModelCreation as mc

if __name__ == "__main__":
    coins = ["BTCUSDC", "ETHUSDC", "ADAUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC", "LTCUSDC", "XRPUSDC", "SOLUSDC"]
    for coin in coins:
        mc.AutoLSTM(coin, "24H")
