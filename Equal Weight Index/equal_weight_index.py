"""
Module aims to create an equal weight index using the S&P500 benchmark.

Using a portfolio size in USD to allocate the number of shares to buy
in order to replicate the benchmark index.
Current drawback this module experience is to correctly determine time periods.
"""
from pandas import DataFrame
import yfinance as yf
import warnings
import yf_tools
warnings.filterwarnings('ignore')  # Suppress warnings

"""
Load the S&P500 tickers.
Get the marketcap for each company.
Get the last closing price available.
Allocate the number of shares to buy based on the porftolio size.
"""
portfolio_size: int = 10_000_000  # Portfolio size in dollars

# Get current S&P500 tickers
tickers: DataFrame = yf_tools.get_sp500_tickers()

# Get marketcap
market_cap_df: DataFrame = yf_tools.get_ticker_info(tickers.Symbol.to_list(),
                                                    ['marketCap'])\
    .reset_index(names=['Symbol'])

# Get latest closing prices
underlyings_ovw: DataFrame = yf.download(tickers['Symbol'].tolist(),
                                         period='1d')['Close'].iloc[-1]\
    .reset_index()
underlyings_ovw.columns = ['Symbol', 'Price']

# Add the market cap
underlyings_ovw: DataFrame = underlyings_ovw.merge(market_cap_df,
                                                   how='inner', on='Symbol')

# Calculate the number of shares to replicate S&P500 index
yf_tools.allocate_shares(underlyings_ovw, portfolio_size,
                         'Price', 'num_of_shares_to_buy')

underlyings_ovw.to_csv('equal_weight_index.csv', index=False)
