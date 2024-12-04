from backtesting import Backtest, Strategy
from backtesting.test import GOOG
from backtesting.lib import crossover
import talib

class RsiOscilator(Strategy):
    """
    RSI Oscillator Strategy that utilizes the RSI (Relative Strength Index) 
    to generate buy and sell signals based on crossover conditions.
    
    - Sells or reverses to a short position if the daily RSI crosses below 
      the upper bound and an existing long position is open.
    - Buys or reverses to a long position if the daily RSI crosses above 
      the lower bound and no long position is open.
    """
    
    upper_bound = 70  # RSI level indicating overbought conditions
    lower_bound = 30  # RSI level indicating oversold conditions
    rsi_window = 14   # Look-back period for calculating the RSI

    def init(self):
        """
        Initializes the daily RSI indicator based on the closing price and 
        the specified `rsi_window`. The RSI will be used to assess market 
        conditions for buy and sell signals.
        """
        self.daily_rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)
    
    def next(self):
        """
        Defines the core trading logic for each time step:
        
        - If the daily RSI crosses below the upper bound and the current 
          position is long, the position is closed and a sell order is executed.
        - If the daily RSI crosses above the lower bound and the current 
          position is either short or flat, the position is closed and a 
          buy order is executed.
        """
        if crossover(self.daily_rsi, self.upper_bound):
            if self.position.is_long:
                self.position.close()
                self.sell()
                
        elif crossover(self.lower_bound, self.daily_rsi):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()

# Initialize and run the backtest with starting cash of 10,000
bt = Backtest(GOOG, RsiOscilator, cash=10_000)

# Run the backtest and print the resulting statistics
stats = bt.run()
print(stats)

# Optimize the backtest by finding the best RSI parameters
stats = bt.optimize(
    upper_bound=range(10, 85, 5),       # Range for the upper RSI bound (overbought level)
    lower_bound=range(10, 85, 5),       # Range for the lower RSI bound (oversold level)
    rsi_window=range(10, 30, 2),        # Range for the RSI calculation window sizes
    maximize='Sharpe Ratio',            # Objective: maximize the Sharpe Ratio
    constraint=lambda param: param.upper_bound > param.lower_bound  # Ensure logical parameter constraints
)
