import datetime as dt
import yfinance as yf

from backtesting import Backtest, Strategy
from backtesting.test import GOOG
from backtesting.lib import crossover, resample_apply
import talib

class RsiOscilator(Strategy):
    
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    
    def init(self):
        self.daily_rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)
        self.weekly_rsi = resample_apply('4H', talib.RSI,
                                         self.data.Close, self.rsi_window)
    
    def next(self):
        
        if (crossover(self.daily_rsi, self.upper_bound))\
            and (self.weekly_rsi[-1] > self.upper_bound):
            self.position.close()
        elif (crossover(self.lower_bound, self.daily_rsi))\
            and (self.weekly_rsi[-1] < self.lower_bound):
            self.buy()
            



# Set the end date and start date for data download
end_date = dt.datetime.today().date()

# Download 1-hour interval data for 'GOOG' from Yahoo Finance
prices_df = yf.download('GOOG', interval='1h', start='2024-06-01', end=end_date)[['Open', 'High', 'Low', 'Close']]

# Ensure the data is in a pandas DataFrame
prices_df.columns = prices_df.columns.get_level_values(0)

# Resample data to 4-hour (4H) intervals for OHLC values
data_4h = prices_df.resample('4H').agg({
    'Open': 'first', 
    'High': 'max', 
    'Low': 'min', 
    'Close': 'last'
}).dropna()  # Drop any rows with NaN values

bt = Backtest(prices_df, RsiOscilator, cash=10_000)

stats = bt.run()
print(stats)

# Important the use of constraint to apply a bit of a twist
# stats = bt.optimize(
#     upper_bound=range(10, 85, 5),
#     lower_bound=range(10,85,5),
#     rsi_window=range(10,30,2),
#     maximize='Sharpe Ratio',
#     constraint=lambda param: param.upper_bound > param.lower_bound)