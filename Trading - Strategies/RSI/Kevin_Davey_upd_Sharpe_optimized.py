from backtesting import Backtest, Strategy
import talib  # Import TA-Lib for technical indicators
import numpy as np
from polygon_io import out_df


class CustomStrategy(Strategy):
    """
    A trading strategy that utilizes ATR (Average True Range) and RSI (Relative Strength Index)
    indicators, combined with high-level breakout conditions, to manage trade entries, exits,
    stop-losses, and take-profit targets.
    """

    # Define parameters for optimization
    atr_multiplier_loss = 1.5  # Multiplier for ATR-based stop loss
    atr_multiplier_profit = 2.0  # Multiplier for ATR-based profit target
    rsi_period = 35  # Look-back period for RSI calculation
    high_period = 20  # Look-back period for highest close level calculation

    def init(self):
        """
        Initializes the necessary indicators and variables for the strategy.
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
        self.atr = self.I(talib.SMA, tr, 14)  # ATR look-back period is fixed for now
        
        # RSI for gauging market momentum and overbought/oversold conditions
        self.rsi = self.I(talib.RSI, close, self.rsi_period)

        # Track the highest close for breakout conditions
        self.highest_close = self.I(talib.MAX, close, self.high_period)

    def next(self):
        """
        Defines the core trading logic to be executed on each new bar (time step).
        """
        # Calculate stop-loss and take-profit levels based on ATR
        atr_value = self.atr[-1]
        stop_loss = self.data.Close[-1] - self.atr_multiplier_loss * atr_value
        take_profit = self.data.Close[-1] + self.atr_multiplier_profit * atr_value

        # Long Entry Condition: Buy if breakout conditions are met and RSI indicates bullish momentum
        if self.data.Close[-1] >= self.highest_close[-1] and self.rsi[-1] > 50:
            if not self.position.is_long:
                self.buy(sl=stop_loss, tp=take_profit)


# Backtest and Optimization
bt = Backtest(out_df, CustomStrategy, cash=10000, commission=0.002)

stats = bt.run()
# # Optimize parameters
# stats = bt.optimize(
#     atr_multiplier_loss=[1.0, 1.2, 1.5, 1.8, 2.0],  # Test ATR stop multipliers
#     atr_multiplier_profit=[1.5, 2.0, 2.5, 3.0],  # Test ATR profit multipliers
#     rsi_period=list(range(10, 40, 5)),  # Test RSI periods from 10 to 40 in steps of 5
#     high_period=list(range(20, 60, 5)),  # Test breakout look-back periods
#     maximize='Sharpe Ratio',  # Optimize for Sharpe Ratio
# )

print(stats)
# Uncomment to plot the optimized backtest results
# bt.plot()
