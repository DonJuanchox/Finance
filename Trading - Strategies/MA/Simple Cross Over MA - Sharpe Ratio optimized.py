from backtesting import Backtest, Strategy
import talib
import numpy as np
from backtesting.test import GOOG  # Replace with a suitable dataset

class SharpeRatioTargetStrategy(Strategy):
    """
    Strategy designed to maximize the Sharpe Ratio by leveraging a moving average crossover
    for entry signals, combined with an ATR-based stop-loss and trailing stop.
    
    - Long Entry: Triggered when the short-term SMA crosses above the long-term SMA.
    - Stop Loss: Set based on ATR (Average True Range) to accommodate market volatility.
    - Trailing Stop: Adjusted dynamically based on ATR to lock in profits as price moves in favor.
    """

    # Define strategy parameters
    short_sma_period = 20  # Period for the short-term SMA
    long_sma_period = 50  # Period for the long-term SMA
    atr_period = 14  # Period for ATR calculation
    atr_multiplier = 1.5  # Multiplier for ATR-based stop-loss and trailing stop

    def init(self):
        """
        Initializes indicators and variables for the strategy.
        
        - Sets up short and long simple moving averages (SMAs) for crossover entry signals.
        - Calculates ATR (Average True Range) for volatility-based stop-loss and trailing stop adjustments.
        - Initializes a variable to store the trailing stop value for an open position.
        """
        # Short and Long SMAs for entry signals
        self.short_sma = self.I(talib.SMA, self.data.Close, self.short_sma_period)
        self.long_sma = self.I(talib.SMA, self.data.Close, self.long_sma_period)

        # ATR for stop-loss and trailing stop calculations
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)

        # Variable to track the trailing stop for an open position
        self.trailing_stop = None

    def next(self):
        """
        Defines the trading logic executed on each new bar (time step):
        
        - Long Entry Condition: Triggers a buy if the short SMA is above the long SMA and no long position is open.
        - Initial Stop Loss: Sets a stop loss at a distance based on ATR from the entry price.
        - Trailing Stop Management: Adjusts the trailing stop if the price moves favorably, locking in profits.
        - Position Exit: Closes the position if the current price falls below the trailing stop.
        """
        # Check for long entry signal based on SMA crossover
        if self.short_sma[-1] > self.long_sma[-1] and not self.position.is_long:
            # Calculate initial stop loss based on ATR
            atr_value = self.atr[-1]
            entry_price = self.data.Close[-1]
            stop_loss = entry_price - self.atr_multiplier * atr_value

            # Enter long position and set initial trailing stop
            self.buy(sl=stop_loss)
            self.trailing_stop = entry_price - atr_value * self.atr_multiplier

        # Manage trailing stop for an open long position
        if self.position.is_long:
            # Adjust the trailing stop if price has moved up, tightening the stop
            new_trailing_stop = self.data.Close[-1] - self.atr_multiplier * self.atr[-1]
            if new_trailing_stop > self.trailing_stop:
                self.trailing_stop = new_trailing_stop

            # Exit position if the current price drops below the trailing stop
            if self.data.Close[-1] < self.trailing_stop:
                self.position.close()

# Running the Backtest with example data
import pathlib
import pandas as pd

data = pathlib.Path(r'C:\Users\juann\OneDrive\Documentos\GitHub\Finance\Trading - Strategies\MSFT_2024.csv')
df = pd.read_csv(data, delimiter=';')
df.columns = df.columns.str.capitalize()

df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df.set_index('Timestamp', inplace=True)

# Resampling the data into 5-minute intervals
resampled_df = df.resample('4h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).interpolate()



bt = Backtest(df, SharpeRatioTargetStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
# Uncomment below to plot the backtest results
# bt.plot()

