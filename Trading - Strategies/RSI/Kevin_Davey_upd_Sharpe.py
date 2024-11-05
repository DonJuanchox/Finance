from backtesting import Backtest, Strategy
import talib  # Import TA-Lib for technical indicators
import numpy as np
from backtesting.test import GOOG

class CustomStrategy(Strategy):
    """
    A trading strategy that utilizes ATR (Average True Range) and RSI (Relative Strength Index)
    indicators, combined with high-level breakout conditions, to manage trade entries, exits,
    stop-losses, and take-profit targets.

    - Sets a fixed dollar stop-loss, an ATR-based stop-loss, and an ATR-based profit target.
    - Executes long entries based on breakout conditions and RSI values.
    - Adjusts waiting periods based on the outcome of each trade.
    """

    # Define parameters for the strategy
    dollar_stop = 1000  # Fixed dollar stop loss amount
    atr_multiplier_loss = 1.5  # Multiplier for ATR-based stop loss
    atr_multiplier_profit = 2.0  # Multiplier for ATR-based profit target
    rsi_period = 30  # Look-back period for RSI calculation
    atr_period = 14  # Look-back period for ATR calculation
    high_period = 48  # Look-back period for highest close level calculation

    def init(self):
        """
        Initializes the necessary indicators and variables for the strategy.

        - Calculates True Range (TR) manually for accurate ATR computation.
        - Sets up the ATR for volatility-based stop-loss and profit targets.
        - Calculates RSI for momentum tracking.
        - Tracks the 48-bar highest close for breakout-based entry conditions.
        - Initializes variables to store the outcome of the last trade and a wait counter.
        """
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Calculate True Range (TR) manually to avoid dependency on data shifting
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - np.roll(close, 1)),
                abs(low - np.roll(close, 1))
            )
        )
        tr[0] = 0  # Set the first TR value to 0, since there's no previous close for comparison
        
        # Calculate ATR (Average True Range) using a simple moving average of TR
        self.atr = self.I(talib.SMA, tr, self.atr_period)
        
        # RSI for gauging market momentum and overbought/oversold conditions
        self.rsi = self.I(talib.RSI, close, self.rsi_period)

        # Track the 48-bar highest close for breakout conditions
        self.highest_close = self.I(talib.MAX, close, self.high_period)
        
        # Track the outcome of the last trade and initialize the wait period counter
        self.last_trade_won = None
        self.wait_bars = 0

    def next(self):
        """
        Defines the core trading logic to be executed on each new bar (time step):
        
        - Waits if the strategy is in a cooldown period after a trade.
        - Sets ATR-based stop-loss and take-profit levels dynamically.
        - Long Entry Condition: Buys if the price breaks above the highest close level
          and RSI is above 50.
        """
        # Skip if in a cooldown period after a recent trade
        if self.wait_bars > 0:
            self.wait_bars -= 1
            return

        # Calculate stop-loss and take-profit levels based on ATR and fixed dollar stop
        atr_value = self.atr[-1]
        stop_loss = self.dollar_stop / self.data.Close[-1]
        atr_stop = self.atr_multiplier_loss * atr_value
        atr_profit = self.atr_multiplier_profit * atr_value

        # Long Entry Condition: Buy if breakout conditions are met and RSI indicates bullish momentum
        if self.data.Close[-1] >= self.highest_close[-1] and self.rsi[-1] > 50:
            if not self.position.is_long:
                self.buy(sl=self.data.Close[-1] - max(stop_loss, atr_stop),
                         tp=self.data.Close[-1] + atr_profit)

    def on_trade_exit(self, trade):
        """
        Handles actions on trade exit, specifically adjusting the cooldown period based on
        whether the last trade was profitable or not.
        
        - Sets `wait_bars` to 20 bars if the last trade was profitable, otherwise to 5 bars.
        - Tracks the result of the last trade for potential analysis.
        """
        self.last_trade_won = trade.pl > 0
        self.wait_bars = 20 if self.last_trade_won else 5

# Backtest setup with example data (GOOG)
bt = Backtest(GOOG, CustomStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
# Uncomment to plot the backtest results
# bt.plot()
