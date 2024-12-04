import yf_tools
import yfinance as yf
import datetime as dt

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib

class RsiOscilator(Strategy):
    """
    RSI Oscillator strategy that uses the RSI (Relative Strength Index) to generate buy and sell signals.
    A buy signal is generated when the RSI crosses above the lower bound, indicating an oversold condition.
    A sell signal is generated when the RSI crosses below the upper bound, indicating an overbought condition.
    """
    
    upper_bound = 70  # Upper bound for RSI indicating overbought condition
    lower_bound = 30  # Lower bound for RSI indicating oversold condition
    rsi_window = 14   # Window size for calculating RSI
    
    def init(self):
        """
        Initializes the RSI indicator using the closing prices of the data.
        The RSI indicator is calculated using the specified window (rsi_window).
        """
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)
    
    def next(self):
        """
        Defines the logic for each step in the backtesting process.
        
        - Closes the current position if the RSI crosses below the upper bound (indicating an overbought condition).
        - Buys if the RSI crosses above the lower bound (indicating an oversold condition).
        """
        if crossover(self.rsi, self.upper_bound):
            self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            self.buy()

# Get backtesting data
end_date = dt.datetime.today().date()
prices_df = yf.download('GOOG', end=end_date)[['Open', 'High', 'Low', 'Close']]
prices_df.columns = prices_df.columns.get_level_values(0)

# Initialize and run the backtest
bt = Backtest(prices_df, RsiOscilator)

# Run the backtest with default parameters
stats = bt.run()

# Optimize the backtest by finding the best parameters for upper_bound, lower_bound, and rsi_window
stats = bt.optimize(
    upper_bound=range(10, 85, 5),    # Range for upper RSI bound (overbought level)
    lower_bound=range(10, 85, 5),    # Range for lower RSI bound (oversold level)
    rsi_window=range(10, 30, 2),     # Range for RSI window sizes
    maximize='Sharpe Ratio',         # Metric to maximize during optimization
    constraint=lambda param: param.upper_bound > param.lower_bound  # Constraint to ensure logical bounds
)
