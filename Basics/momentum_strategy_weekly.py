"""
Module aims to develop a momentum strategy to analyze stocks.

Using the S&P500 underlyings to calculate momentum over weekly periods.
The script calculates momentum for 1 week, 2 weeks, 4 weeks, and 12 weeks.
"""

import etl_logger
import yf_tools

import pandas as pd
import logging
import datetime as dt
from typing import List, Dict
from numpy import ndarray
from pandas.tseries.offsets import BusinessDay
from datetime import timedelta
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')


def calculate_weekly_returns(df: pd.DataFrame,
                             logger: logging.Logger,
                             start_date: dt.date,
                             time_periods: List[str],
                             weekly_offsets: List[int]) -> Dict[str, ndarray]:
    """
    Calculate weekly returns for specified time periods and offsets.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame indexed by dates containing financial data.
    logger : logging.Logger
        Logger object.
    start_date : dt.date
        Start date from which offsets are calculated, in the format `%Y-%m-%d`.
    time_periods : List[str]
        List representing labels for each period (e.g., ['1W', '2W', '4W']).
    weekly_offsets : List[int]
        List containing number of days to offset from the start_date.

    Returns
    -------
    weekly_returns : Dict[str, np.ndarray]
        Dictionary where key is a period label from 'time_periods',
        and the value is an array of financial data corresponding
        to the adjusted date.

    Notes
    -----
    - The function expects `df` to be indexed by dates in UTC time.
    - If the calculated offset date does not exist in the DataFrame index,
      the function defaults to the previous business day.
    """
    if len(time_periods) != len(weekly_offsets):
        raise ValueError('List must have the same number of elements')

    weekly_returns = {}

    for period, offset in zip(time_periods, weekly_offsets):
        idx_date = start_date + timedelta(days=offset)
        if idx_date in df.index:
            weekly_returns[period] = df.loc[idx_date].values
        else:
            logger.warning(f'The following date: {idx_date} not in DataFrame')
            previous_bday = (idx_date - BusinessDay(n=1)).tz_localize('UTC')
            weekly_returns[period] = df.loc[previous_bday].values
    return weekly_returns


def calculate_hqm_score(df: pd.DataFrame,
                        percentile_columns: List[str]) -> pd.DataFrame:
    """
    Calculate the HQM Score for underlying based on percentiles values.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing financial data.
    percentile_columns : List[str]
        DataFrame columns which store percentile values for a given underlying.

    Returns
    -------
    df : pd.DataFrame
        Original DataFrame containing HQM score.

    """
    df['HQM Score'] = df[percentile_columns].mean(axis=1)


# Get logger
console = logging.StreamHandler()
logger = etl_logger.get_logger('momentum', logging.WARNING, [console])
logger.info('Running')

# Define variables
portfolio_size: int = 10_000_000  # Portfolio size in dollars
weekly_offsets = [7, 14, 28, 84]  # Weekly offsets in days
end_date = dt.datetime(2024, 11, 18)  # Define date range for data retrieval
start_date = dt.datetime(2023, 11, 18)

# Get S&P 500 tickers and stock data
sp500_underlyings = yf_tools.get_sp500_tickers(logger)

if sp500_underlyings.empty:
    raise Exception('Data is empty')
else:
    sp_tickers = sp500_underlyings['Symbol'].to_list()
    try:
        closing_prices = yf.download(sp_tickers, start=start_date, end=end_date)['Close']
        if closing_prices.empty:
            raise Exception('Data is empty')

    except Exception as e:
        logger.error(f"Error downloading stock data: {e}")
        raise e

# Calculate daily returns and cumulative returns
closing_prices_pct = closing_prices.pct_change()
returns = (1 + closing_prices_pct).cumprod() - 1

# Calculate weekly returns for each period
time_periods = ['1W return', '2W return', '4W return', '12W return']
return_values = calculate_weekly_returns(returns, logger, start_date,
                                         time_periods, weekly_offsets)

# Prepare main watchlist DataFrame
watchlist = pd.DataFrame({
    'Symbol': sp500_underlyings['Symbol'],
    **{period: return_values.get(period, pd.Series(dtype='float64'))
        for period in time_periods},
    **{f'{period} percentile': None for period in time_periods},
    'HQM Score': None
}).fillna(0)

# Calculate percentiles and HQM score
percentiles = [f'{period} percentile' for period in time_periods]
yf_tools.calculate_percentiles(watchlist, time_periods, percentiles)
calculate_hqm_score(watchlist, percentiles)

# Merge last closing price and allocate shares
last_close = closing_prices.iloc[-1].reset_index()
last_close.columns = ['Symbol', 'Close Price']
watchlist = watchlist.merge(last_close, how='inner', on='Symbol')

yf_tools.allocate_shares(watchlist, portfolio_size,
                         'Close Price', 'Num_shares_to_buy')

# Sort by HQM Score and select top 50
watchlist.sort_values('HQM Score', ascending=False, inplace=True)
top_50_momentum = watchlist.head(50).reset_index(drop=True)

top_50_momentum.to_csv('weekly_momentum_strategy.csv')
