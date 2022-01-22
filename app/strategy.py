from datetime import datetime

import numpy as np
import talib
from matplotlib import pyplot as plt


class Strategy:

    def __init__(self, indicator_name, strategy_name, pair, interval, klines):
        # Name of indicator
        self.indicator = indicator_name
        # Name of strategy being used
        self.strategy = strategy_name
        # Trading pair
        self.pair = pair
        # Trading interval
        self.interval = interval
        # Kline data for the pair on given interval
        self.klines = klines
        # Calculates the indicator
        self.indicator_result = self.calculateIndicator()
        # Uses the indicator to run strategy
        self.strategy_result = self.calculateStrategy()
        # Determine if is bought
        self.is_bought = False

    '''
    Calculates the desired indicator given the init parameters
    '''

    def calculateIndicator(self):
        if self.indicator == 'MACD':
            close = [float(entry[4]) for entry in self.klines]
            close_array = np.array(close)

            macd, macdsignal, macdhist = talib.MACD(close_array, fastperiod=12, slowperiod=26, signalperiod=9)
            return [macd, macdsignal, macdhist]

        elif self.indicator == 'RSI':
            close = [float(entry[4]) for entry in self.klines]
            close_array = np.array(close)

            rsi = talib.RSI(close_array, timeperiod=14)
            return rsi
        else:
            return None

    '''
    Runs the desired strategy given the indicator results
    '''

    def calculateStrategy(self):
        if self.indicator == 'MACD':
            if self.strategy == 'CROSS':
                open_time = [int(entry[0]) for entry in self.klines]
                new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
                self.time = new_time
                crosses = []
                macdabove = False
                # Runs through each timestamp in order
                for i in range(len(self.indicator_result[0])):
                    if np.isnan(self.indicator_result[0][i]) or np.isnan(self.indicator_result[1][i]):
                        pass
                    # If both the MACD and signal are well defined, we compare the 2 and decide if a cross has occured
                    else:
                        if self.indicator_result[0][i] > self.indicator_result[1][i]:
                            if macdabove == False:
                                macdabove = True
                                # Appends the timestamp, MACD value at the timestamp, color of dot, buy signal, and the buy price
                                cross = [new_time[i], self.indicator_result[0][i], 'go', 'BUY', self.klines[i][4]]
                                crosses.append(cross)
                        else:
                            if macdabove == True:
                                macdabove = False
                                # Appends the timestamp, MACD value at the timestamp, color of dot, sell signal, and the sell price
                                cross = [new_time[i], self.indicator_result[0][i], 'ro', 'SELL', self.klines[i][4]]
                                crosses.append(cross)
                return crosses

            else:
                return None
        elif self.indicator == 'RSI':
            if self.strategy == '7030':
                open_time = [int(entry[0]) for entry in self.klines]
                new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
                self.time = new_time
                result = []
                active_buy = False
                # Runs through each timestamp in order
                for i in range(len(self.indicator_result)):
                    if np.isnan(self.indicator_result[i]):
                        pass
                    # If the RSI is well defined, check if over 70 or under 30
                    else:
                        if float(self.indicator_result[i]) < 30 and active_buy == False:
                            # Appends the timestamp, RSI value at the timestamp, color of dot, buy signal, and the
                            # buy price
                            entry = [new_time[i], self.indicator_result[i], 'go', 'BUY', self.klines[i][4]]
                            result.append(entry)
                            active_buy = True
                        elif float(self.indicator_result[i]) > 70 and active_buy == True:
                            # Appends the timestamp, RSI value at the timestamp, color of dot, sell signal, and the
                            # sell price
                            entry = [new_time[i], self.indicator_result[i], 'ro', 'SELL', self.klines[i][4]]
                            result.append(entry)
                            active_buy = False
                return result
            elif self.strategy == '8020':
                open_time = [int(entry[0]) for entry in self.klines]
                new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
                self.time = new_time
                result = []
                active_buy = False
                # Runs through each timestamp in order
                for i in range(len(self.indicator_result)):
                    if np.isnan(self.indicator_result[i]):
                        pass
                    # If the RSI is well defined, check if over 80 or under 20
                    else:
                        if float(self.indicator_result[i]) < 20 and active_buy == False:
                            # Appends the timestamp, RSI value at the timestamp, color of dot, buy signal, and the
                            # buy price
                            entry = [new_time[i], self.indicator_result[i], 'go', 'BUY', self.klines[i][4]]
                            result.append(entry)
                            active_buy = True
                        elif float(self.indicator_result[i]) > 80 and active_buy == True:
                            # Appends the timestamp, RSI value at the timestamp, color of dot, sell signal, and the
                            # sell price
                            entry = [new_time[i], self.indicator_result[i], 'ro', 'SELL', self.klines[i][4]]
                            result.append(entry)
                            active_buy = False
                return result
        else:
            return None

    def buyOrSell(self):
        return self.strategy_result[-1][3]
        pass

    '''
    Getter for the strategy result
    '''

    def getStrategyResult(self):
        return self.strategy_result

    '''
    Getter for the klines
    '''

    def getKlines(self):
        return self.klines

    '''
    Getter for the trading pair
    '''

    def getPair(self):
        return self.pair

    '''
    Getter for the trading interval
    '''

    def getInterval(self):
        return self.interval

    '''
    Getter for the time list
    '''

    def getTime(self):
        return self.time

    '''
    Plots the desired indicator with strategy buy and sell points
    '''

    def plotIndicator(self):
        open_time = [int(entry[0]) for entry in self.klines]
        new_time = [datetime.fromtimestamp(time / 1000) for time in open_time]
        plt.style.use('dark_background')
        for entry in self.strategy_result:
            plt.plot(entry[0], entry[1], entry[2])
        if self.indicator == 'MACD':
            plt.plot(new_time, self.indicator_result[0], label='MACD')
            plt.plot(new_time, self.indicator_result[1], label='MACD Signal')
            plt.plot(new_time, self.indicator_result[2], label='MACD Histogram')

        elif self.indicator == 'RSI':
            plt.plot(new_time, self.indicator_result, label='RSI')

        else:
            pass

        title = self.indicator + " Plot for " + self.pair + " on " + str(self.interval)
        plt.title(title)
        plt.xlabel("Open Time")
        plt.ylabel("Value")
        plt.legend()
        plt.show()
