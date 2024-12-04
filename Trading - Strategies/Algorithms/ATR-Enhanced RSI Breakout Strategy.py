  """
ATR-Enhanced RSI Breakout Strategy

This strategy combines momentum and breakout signals with robust risk management 
using the Average True Range (ATR). It identifies bullish market conditions and 
enters long positions when specific conditions are met, while managing exits 
through ATR-based stop-loss and take-profit levels.

**Strategy Components:**
1. **Breakout Condition:**
   - The strategy looks for the price to close above the highest closing price 
     over a specified period (`high_period`).
   - A filter is applied using the RSI (Relative Strength Index), requiring it 
     to be above 50 to confirm momentum.

2. **Risk Management:**
   - Stop-loss and take-profit levels are calculated based on ATR:
     - Stop-loss is the greater of a dollar-defined risk (`dollar_stop`) or an 
       ATR-based multiple (`atr_multiplier_loss`).
     - Take-profit is set as a multiple of ATR (`atr_multiplier_profit`).

3. **Cooldown Period:**
   - After a trade exits, a cooldown period (`wait_bars`) is applied:
     - If the trade was profitable, the cooldown is longer.
     - If the trade was a loss, the cooldown is shorter.

**Parameters:**
- `dollar_stop`: Fixed dollar amount used to calculate the minimum stop-loss level.
- `atr_multiplier_loss`: Multiplier for ATR to calculate the stop-loss.
- `atr_multiplier_profit`: Multiplier for ATR to calculate the take-profit.
- `rsi_period`: Period for RSI calculation.
- `atr_period`: Period for ATR calculation.
- `high_period`: Look-back period for identifying the highest close.

**Workflow:**
1. On initialization (`init`):
   - Compute indicators: ATR, RSI, and the highest close over `high_period`.
2. On each bar (`next`):
   - Check if cooldown period is active; skip execution if so.
   - For trade entry:
     - Enter a long position if the price is above the `highest_close` and RSI > 50.
     - Set stop-loss (`sl`) and take-profit (`tp`) levels upon entry.
   - For trade management:
     - Exit the trade if the price hits the stop-loss or take-profit levels.
     - Adjust cooldown period based on trade outcome.

**Backtesting and Optimization:**
- The strategy can be backtested with historical price data containing Open, High, Low, Close, and Volume.
- It allows optimization of parameters, such as `atr_multiplier_profit`, to maximize performance metrics like Sharpe Ratio.

"""
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import numpy as np
import pandas as pd
from polygon_load_data import out_df  # Ensure `out_df` is structured with necessary columns


class CustomStrategy(Strategy):
    dollar_stop = 1000
    atr_multiplier_loss = 1.0
    atr_multiplier_profit = 3.4
    rsi_period = 10
    atr_period = 14
    high_period = 90

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
stats = bt.run()
print(stats)
# Run optimization
# stats = bt.optimize(
#     atr_multiplier_profit=np.arange(1.5, 10, 0.05).tolist(),
#     maximize='Sharpe Ratio',
# )

# # Print the best parameters
# print("Optimized Parameters:")
# print(stats._strategy)

# print(stats)