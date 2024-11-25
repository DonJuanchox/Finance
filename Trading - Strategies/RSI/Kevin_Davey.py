from backtesting import Backtest, Strategy
import talib  # Import TA-Lib for technical indicators
import numpy as np
from polygon_io import out_df

class CustomStrategy(Strategy):
    """
    Custom trading strategy by Kevin Davey, employing ATR-based and RSI indicators
    along with breakout levels for entry signals, stop losses, and profit targets.

    - A fixed dollar stop loss is set alongside an ATR-based stop and profit target.
    - Long and short positions are entered based on breakout conditions and RSI levels.
    - Includes a cooldown period after each trade, with a longer wait following profitable trades.
    """

    # Strategy parameters
    dollar_stop = 1000  # Fixed dollar amount for stop loss
    atr_multiplier_loss = 1.5  # Multiplier for ATR stop loss level
    atr_multiplier_profit = 2.0  # Multiplier for ATR profit target level
    rsi_period = 30  # Look-back period for RSI calculation
    atr_period = 14  # Look-back period for ATR calculation
    high_period = 48  # Look-back period for highest/lowest close levels

    def init(self):
        """
        Initializes indicators and variables required for the strategy.
        
        - Calculates the True Range (TR) manually to define the Average True Range (ATR).
        - Initializes the ATR for setting dynamic stop-loss and profit targets.
        - Sets the RSI indicator for identifying market momentum.
        - Tracks the highest and lowest close levels over a 48-bar period.
        - Sets up variables to record the last trade result and the wait period between trades.
        """
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Calculate True Range (TR) manually without using .shift()
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - np.roll(close, 1)),
                abs(low - np.roll(close, 1))
            )
        )
        tr[0] = 0  # Set the first TR value to 0 since there's no previous close for reference
        
        # Calculate ATR (Average True Range) using the SMA of the TR over the specified period
        self.atr = self.I(talib.SMA, tr, self.atr_period)
        
        # RSI indicator to gauge market momentum
        self.rsi = self.I(talib.RSI, close, self.rsi_period)

        # Track 48-bar highest and lowest close values for breakout signals
        self.highest_close = self.I(talib.MAX, close, self.high_period)
        self.lowest_close = self.I(talib.MIN, close, self.high_period)
        
        # Track the outcome of the last trade and initialize the waiting period
        self.last_trade_won = None
        self.wait_bars = 0

    def next(self):
        """
        Executes trade logic on each new bar:
        
        - Waits for the cooldown period to expire after each trade.
        - Calculates stop-loss and take-profit levels based on ATR and dollar stop.
        - Enters a long position if the close is at or above the highest close level 
          and RSI is greater than 50.
        - Enters a short position if the close is at or below the lowest close level 
          and RSI is less than 50.
        """
        # Decrease the wait counter if in a cooldown period
        if self.wait_bars > 0:
            self.wait_bars -= 1
            return

        # Calculate dynamic stop-loss and take-profit levels using ATR and dollar stop
        atr_value = self.atr[-1]
        stop_loss = self.dollar_stop / self.data.Close[-1]
        atr_stop = self.atr_multiplier_loss * atr_value
        atr_profit = self.atr_multiplier_profit * atr_value

        # Long Entry Condition
        if self.data.Close[-1] >= self.highest_close[-1] and self.rsi[-1] > 50:
            if not self.position.is_long:
                self.buy(sl=self.data.Close[-1] - max(stop_loss, atr_stop),
                         tp=self.data.Close[-1] + atr_profit)
        
        # Short Entry Condition
        elif self.data.Close[-1] <= self.lowest_close[-1] and self.rsi[-1] < 50:
            if not self.position.is_short:
                self.sell(sl=self.data.Close[-1] + max(stop_loss, atr_stop),
                          tp=self.data.Close[-1] - atr_profit)

    def on_trade_exit(self, trade):
        """
        Event handler for when a trade is closed.
        
        - Sets a waiting period after each trade, with a 20-bar wait if the last trade 
          was profitable, and a 5-bar wait if it was not.
        """
        self.last_trade_won = trade.pl > 0
        self.wait_bars = 20 if self.last_trade_won else 5

# Backtest with example data (replace GOOG with your own dataset)
bt = Backtest(out_df, CustomStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
# Uncomment below to plot the backtest results
# bt.plot()
