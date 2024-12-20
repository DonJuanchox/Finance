from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import numpy as np
import pandas as pd
from polygon_load_data import out_df


class CustomStrategy(Strategy):
    dollar_stop = 1000
    atr_multiplier_loss = 1.5
    atr_multiplier_profit = 2.0
    rsi_period = 35
    atr_period = 14
    high_period = 20

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Calculate True Range (TR)
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - np.roll(close, 1)),
                abs(low - np.roll(close, 1))
            )
        )
        tr[0] = 0  # First TR value
        self.atr = self.I(lambda x: talib.SMA(x, self.atr_period), tr)

        # RSI
        self.rsi = self.I(talib.RSI, close, self.rsi_period)

        # Highest close
        self.highest_close = self.I(lambda x: talib.MAX(x, self.high_period), close)

        # Trade management variables
        self.last_trade_won = None
        self.wait_bars = 0

        # Stop-loss and take-profit tracking
        self.sl = None
        self.tp = None

    def next(self):
        # Cooldown period
        if self.wait_bars > 0:
            self.wait_bars -= 1
            return

        # ATR-based levels
        atr_value = self.atr[-1]
        stop_loss = self.dollar_stop / self.data.Close[-1]
        atr_stop = self.atr_multiplier_loss * atr_value
        atr_profit = self.atr_multiplier_profit * atr_value

        # Long Entry
        if self.data.Close[-1] >= self.highest_close[-1] and self.rsi[-1] > 50:
            if not self.position.is_long:
                self.sl = self.data.Close[-1] - max(stop_loss, atr_stop)
                self.tp = self.data.Close[-1] + atr_profit
                self.buy()

        # Trade Exit Logic
        if self.position.is_long:
            if self.data.Close[-1] <= self.sl:
                self.position.close()
                self.on_trade_exit(self.position, won=False)
            elif self.data.Close[-1] >= self.tp:
                self.position.close()
                self.on_trade_exit(self.position, won=True)

    def on_trade_exit(self, trade, won):
        """
        Adjusts the cooldown period based on whether the trade was profitable or not.
        """
        self.last_trade_won = won
        self.wait_bars = 15 if won else 5  # Play around between 15 and 20


# Ensure `out_df` has the required columns
required_columns = {'Open', 'High', 'Low', 'Close', 'Volume'}
if not required_columns.issubset(out_df.columns):
    raise ValueError(f"Input DataFrame must have columns: {required_columns}")

# Backtest
bt = Backtest(out_df, CustomStrategy, cash=10000, commission=.002)
# Run optimization
stats = bt.optimize(
    atr_multiplier_profit=np.arange(1.5, 5.5, 0.05).tolist(),
    maximize='Sharpe Ratio',
)

# Print the best parameters
print("Optimized Parameters:")
print(stats._strategy)

print(stats)

# Uncomment to plot
# bt.plot()
