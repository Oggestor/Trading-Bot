import sys
import os
import numpy as np
import pandas as pd
import random as rand
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from managers import dbManager as db
from standaloneScripts import simulation as sim

def simulateTrade(collection, amount=5000, show=False, stratergy=1, range=2880):
    orginial_amount = amount
    trades = []
    buyPrice = []
    sellPrice = []
    win = []
    prices = []
    timestamps = []
    median_list = []
    mean_list = []
    min_list = []
    max_list = []
    std_list = []
    diff = []
    if stratergy == 1:
        arrays = sim.mergeData(collection)
        for row in zip(*arrays):
            if (row[0] > row[1] and row[0] < row[2] and row[0] < row[3] and
                row[0] < row[4] and row[0] < row[5] and row[0] < row[6] and
                row[0] > row[7] and row[0] < row[8] and row[0] > row[9] and
                row[0] < row[10]):
                    if (len(trades) == 0 or trades[-1] != 'Buy'):
                        trades.append('Buy')
                        buyPrice.append(row[0])
                        if show:
                            print(row[11], 'Buy', row[0])
            elif (
                len(trades) != 0 and row[0] < row[1] and row[0] > row[2] and
                row[0] > row[3] and row[0] > row[4] and row[0] > row[5] and
                row[0] > row[6] and row[0] > row[7] and row[0] > row[8] and
                row[0] > row[9] and row[0] > row[10]):
                    if (trades[-1] != 'Sell' and len(trades) != 0):
                        trades.append('Sell')
                        sellPrice.append(row[0])
                        diff.append((sellPrice[-1]/buyPrice[-1])-1)
                        win.append(row[0]>buyPrice[-1])
                        if show:
                            print(row[11], 'Sell', row[0], (sellPrice[-1]/buyPrice[-1]*amount)-amount, row[0]>buyPrice[-1])
    elif stratergy == 2:  
        arrays = pd.DataFrame(db.getData(collection, "coins"))
        random = rand.randint(0, len(arrays))
        #random = 50000
        print(f'Random number is {random}')
        arrays = arrays.iloc[-random:,:]
        columns = ['price', 'timestamp']
        arrays['price'] = pd.to_numeric(arrays['price'])
        arrays = [arrays[col].to_numpy() for col in columns]
        
        for row in zip(*arrays):
            '''
            This stratergy will be that it will buy when the standard diviation is high and the price is close to the minimum value within 2days,
            and then sell when the price is close to the maximum value within 2 days with a high stadard diviation.
            
            For Bitcoin ive observd that the highest peaks of standard diviation are around 3% of the price, so I will use that as a threshold.
            '''
            prices.append(row[0])
            timestamps.append(row[1])  # Assuming the timestamp is at index 11

            if len(prices) > range:
                # Calculate statistics for the window of the last 2880 prices
                median_list.append(np.median(prices[-range:]))
                mean_list.append(np.mean(prices[-range:]))
                min_list.append(np.min(prices[-range:]))
                max_list.append(np.max(prices[-range:])) 
                std_list.append(np.std(prices[-range:]))
                
                # some kind of swapping logic, this short one kicks in when the price is stable
                if ((std_list[-1]/row[0]>0.01 or std_list[-1]/row[0]<0.005) and row[0] < mean_list[-1]-2*std_list[-1]):

                    if (len(trades) == 0 or trades[-1] != 'Buy'):
                        trades.append('Buy')
                        buyPrice.append(row[0])
                        if show:
                            print(row[1], 'Buy', row[0])
                    # might want to add a hold condition here, when it filles the later condition of row[0] < maen_list[-1]-2*std_list[-1]
                            
                elif ((std_list[-1]/row[0]>0.01 or std_list[-1]/row[0]<0.005) and row[0] > mean_list[-1]+3*std_list[-1]):
                # might want to trade for loss manually? So it only sells for proift? Could alert us if a trade has dropped more than 10%?   
                #elif (row[0] > mean_list[-1] and (len(buyPrice)>0 and (prices[-1] > buyPrice[-1]) or (prices[-1] < buyPrice[-1]*0.6))):    
                    if (len(trades) > 0 and trades[-1] != 'Sell'):
                        trades.append('Sell')
                        sellPrice.append(row[0])
                        diff.append((sellPrice[-1]/buyPrice[-1])-1)
                        win.append(row[0]>buyPrice[-1])
                        amount = amount + ((sellPrice[-1]/buyPrice[-1])-1)*amount
                        if show:
                            print(row[-1], 'Sell', row[0], (sellPrice[-1]/buyPrice[-1]*amount)-amount, row[0]>buyPrice[-1])
    elif stratergy == 3:
        # need to split this up into a big grid
            arrays = sim.mergeData(collection)
            for row in zip(*arrays):
                prices.append(row[0])
                timestamps.append(row[1])
                
                if len(prices) > range:
                    # Calculate statistics for the window of the last 2880 prices
                    median_list.append(np.median(prices[-range:]))
                    mean_list.append(np.mean(prices[-range:]))
                    min_list.append(np.min(prices[-range:]))
                    max_list.append(np.max(prices[-range:])) 
                    std_list.append(np.std(prices[-range:]))
                
                    if (row[0] < row[1] and row[0] < row[2] and row[0] < row[3] and
                        row[0] < row[4] and row[0] < row[5] and row[0] < row[6] and
                        row[0] < row[7] and row[0] < row[8] and row[0] < row[9] and
                        row[0] < row[10]):
                        
                                if (len(trades) == 0 or trades[-1] != 'Buy'):
                                    trades.append('Buy')
                                    buyPrice.append(row[0])
                                    if show:
                                        print(row[11], 'Buy', row[0])
                    elif (
                        len(trades) != 0 and
                        row[0] > row[2]+2*std_list[-1]):
                            if (trades[-1] != 'Sell' and len(trades) != 0):
                                trades.append('Sell')
                                sellPrice.append(row[0])
                                diff.append((sellPrice[-1]/buyPrice[-1])-1)
                                win.append(row[0]>buyPrice[-1])
                                if show:
                                    print(row[11], 'Sell', row[0], (sellPrice[-1]/buyPrice[-1]*amount)-amount, row[0]>buyPrice[-1])
        
    if (len(win) > 0):    
        print(f'The amount of trades that generated profit are {sum(win)} out of {len(win)} which is a success rate of {round(sum(win)/len(win)*100, 2)}%')
    else:
        print(f'No trades were made for {collection[:-4]}')
                
    return sim.calcProfit(diff, orginial_amount, collection)

simulateTrade("BTCUSDC", show = True, stratergy = 2, range=2880)

#480, 840, 1020, 2100, 
#value_list = [2160, 2340, 2880]
#value_list = range(60, 2400, 60)
#for i in value_list:
#    print(i)
#    simulateTrade("DOTUSDC", show = True, stratergy = 2, range=i)

# test to create prediction + - standard diviation of said timeframe