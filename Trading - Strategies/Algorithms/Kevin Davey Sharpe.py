from backtesting import Backtest, Strategy
import talib  # Import TA-Lib for technical indicators
import numpy as np
from polygon_io import out_df


class ImprovedCustomStrategy(Strategy):
    """
    A trading strategy using ATR and RSI indicators, improved with:
    - Trailing stop-loss for locking in profits
    - Time-based exit for stagnant trades
    - Indicator-based exit conditions for better trade management
    """

    # Define parameters for optimization
    atr_multiplier_loss = 1.5  # Multiplier for ATR-based stop loss
    atr_multiplier_profit = 2.0  # Multiplier for ATR-based take profit
    trailing_multiplier = 1.0  # ATR multiplier for trailing stop-loss
    max_holding_period = 20  # Maximum bars to hold a trade
    rsi_period = 35  # Look-back period for RSI calculation
    high_period = 20  # Look-back period for highest close level calculation

    def init(self):
        """
        Initializes indicators and variables for the strategy.
        """
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Calculate True Range (TR) manually to avoid dependency on shifting
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - np.roll(close, 1)),
                abs(low - np.roll(close, 1))
            )
        )
        tr[0] = 0  # Set the first TR value to 0, since there's no previous close for comparison

        # ATR (Average True Range)
        self.atr = self.I(talib.SMA, tr, 14)  # ATR look-back period is fixed for now

        # RSI for gauging market momentum
        self.rsi = self.I(talib.RSI, close, self.rsi_period)

        # Track the highest close for breakout conditions
        self.highest_close = self.I(talib.MAX, close, self.high_period)

        # Variables for trailing stop-loss and trade management
        self.trailing_sl = None
        self.bar_count = 0

    def next(self):
        """
        Defines the trading logic to execute on each new bar.
        """
        # Increment the bar count for tracking holding period
        if self.position:
            self.bar_count += 1

        # Calculate dynamic stop-loss and take-profit levels based on ATR
        atr_value = self.atr[-1]
        initial_stop_loss = self.data.Close[-1] - self.atr_multiplier_loss * atr_value
        initial_take_profit = self.data.Close[-1] + self.atr_multiplier_profit * atr_value

        # Trailing stop-loss adjustment for long positions
        if self.position.is_long:
            self.trailing_sl = max(self.trailing_sl or 0, self.data.Close[-1] - self.trailing_multiplier * atr_value)

            # Exit conditions for long positions
            if self.data.Close[-1] <= self.trailing_sl:  # Trailing stop-loss
                self.position.close()
            elif self.bar_count > self.max_holding_period:  # Time-based exit
                self.position.close()
            elif self.rsi[-1] < 50:  # RSI-based exit
                self.position.close()

        # Trailing stop-loss adjustment for short positions (if implemented)
        # You can add similar logic for short positions.

        # Entry conditions
        if not self.position:
            # Long Entry: Breakout above the highest close with bullish RSI
            if self.data.Close[-1] >= self.highest_close[-1] and self.rsi[-1] > 50:
                self.buy(sl=initial_stop_loss, tp=initial_take_profit)
                self.trailing_sl = self.data.Close[-1] - self.trailing_multiplier * atr_value
                self.bar_count = 0  # Reset bar count on new trade


# Backtest and Optimization
bt = Backtest(out_df, ImprovedCustomStrategy, cash=10000, commission=0.002)

stats = bt.run()
# Uncomment below to optimize the strategy parameters
# stats = bt.optimize(
#     atr_multiplier_loss=[1.0, 1.2, 1.5, 1.8, 2.0],
#     atr_multiplier_profit=[1.5, 2.0, 2.5, 3.0],
#     trailing_multiplier=[0.5, 1.0, 1.5, 2.0],
#     max_holding_period=list(range(10, 40, 5)),
#     rsi_period=list(range(10, 50, 5)),
#     high_period=list(range(10, 60, 5)),
#     maximize='Sharpe Ratio',
# )

print(stats)
# Uncomment to visualize the backtest results
# bt.plot()
