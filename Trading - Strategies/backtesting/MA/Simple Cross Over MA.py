import pandas as pd
from backtesting.lib import SignalStrategy, TrailingStrategy
from backtesting.test import SMA
from backtesting import Backtest
import yfinance as yf
import datetime as dt

class SmaCross(SignalStrategy, TrailingStrategy):
    """
    Strategy that combines simple moving average (SMA) crossover with trailing stop-loss.
    
    - Generates a buy signal when a shorter SMA crosses above a longer SMA.
    - The entry size is set to use 95% of the available liquidity on each signal.
    - Implements a trailing stop-loss at 2 times the average true range (ATR) for each position.
    """
    
    n1 = 30  # Shorter window for SMA (fast moving average)
    n2 = 90  # Longer window for SMA (slow moving average)
    
    def init(self):
        """
        Initializes the strategy by calculating the two moving averages (sma1 and sma2)
        and setting the entry signals based on SMA crossover logic.
        
        - Also calls the superclass init() to ensure proper initialization.
        - Sets the trailing stop-loss using the method provided by `TrailingStrategy`.
        """
        super().init()  # Ensure parent class initialization
        
        # Calculate SMAs for the specified windows
        sma1 = self.I(SMA, self.data.Close, self.n1)
        sma2 = self.I(SMA, self.data.Close, self.n2)
        
        # Create a signal where sma1 crosses above sma2, using a difference method.
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)  # Only long positions (no short selling)
        
        # Set entry size to use 95% of available liquidity for each order
        entry_size = signal * .95
                
        # Apply signal entry sizes using `SignalStrategy` methods
        self.set_signal(entry_size=entry_size)
        
        # Set trailing stop-loss at 2 times the ATR
        self.set_trailing_sl(2)


# Set the end date for downloading stock price data
end_date = dt.datetime.today().date()

# Download historical stock data for 'GOOG' (Google)
prices_df = yf.download('GOOG', end=end_date)[['Open', 'High', 'Low', 'Close']]
prices_df.columns = prices_df.columns.get_level_values(0)  # Flatten multi-level columns if necessary

# Run backtest on the downloaded data with the SmaCross strategy
bt = Backtest(prices_df, SmaCross, commission=.002)

# Print the results of the backtest
print(bt.run())
