"""
Module aims to develop a momentum strategy to analyze stocks.

Using the S&P500 underlyings in order to calculate momentum over a 1 year
span period. Score underlyings under HQM Score which represents xxx.
Current drawback this module experience is to correctly determine time periods.
"""
import etl_logger
import yf_tools

import pandas as pd
import logging
import datetime as dt
from typing import List, Dict
from numpy import ndarray
from pandas.tseries.offsets import BusinessDay
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')


def calculate_monthly_returns(df: pd.DataFrame,
                              logger: logging.Logger,
                              start_date: dt.date,
                              time_periods: List[str],
                              monthly_offsets: List[int]) -> Dict[str, ndarray]:
    """
    Calculate monthly returns for specified time periods and offsets.

    This function computes the monthly returns from a financial DataFrame.
    If a calculated date is not found in the DataFrame index,
    it retrieves the previous business day's value.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame indexed by dates containing financial data,
        such as stock prices or returns.
    logger : logging.Logger
        Logger object.
    start_date : dt.date
        Start date from which offsets are calculated, in the format `%Y-%m-%d`.
    time_periods : List[str]
        List representing labels for each period (e.g., ['1M', '3M', '6M']).
    monthly_offsets : List[int]
        List containing number of months to offset from the start_date.

    Raises
    ------
    ValueError
        Raised if the lengths 'time_periods' & 'monthly_offsets' do not match.

    Returns
    -------
    monthly_returns : Dict[str, np.ndarray]
        Dictionary where key is a period label from 'time_periods',
        and the value is an array of financial data corresponding
        to the adjusted date.

    Notes
    -----
    - The function expects `df` to be indexed by dates in UTC time.
    - If the calculated offset date does not exist in the DataFrame index,
    the function defaults to the previous business day.
    """
    # Check lenght of both lists
    if len(time_periods) != len(monthly_offsets):
        raise ValueError('List must have same number of elements')

    monthly_returns = {}

    for period, offset in zip(time_periods, monthly_offsets):
        # Index date represents start date plus month offset
        # Use walrus operator to assign idx_date(Index date)
        if (idx_date := start_date + pd.DateOffset(months=offset)) in df.index:
            monthly_returns[period] = df.loc[idx_date].values
        else:
            logger.warning(f'The following date: {idx_date} not in DataFrame')
            # Get the previous business date
            previous_bday = (idx_date - BusinessDay(n=1)).tz_localize('UTC')
            monthly_returns[period] = df.loc[previous_bday].values
    return monthly_returns


def calculate_hqm_score(df: pd.DataFrame,
                        percentile_columns: List[str]) -> pd.DataFrame:
    """
    Calculate the HQM Score for underlying based on percentiles values.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing financial data.
    percentile_columns : List[str]
        DataFrame columns which store percile values for a given underlying.

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
from datetime import datetime, timedelta
portfolio_size: int = 10_000_000  # Portfolio size in dollars
monthly_offsets = [1, 3, 6, 12]  # Offsets
end_date = datetime(2024, 1, 1)  # Define date range for data retrieval
start_date = datetime(2023, 1, 30)

"""
Fetch S&P 500 tickers/symbols.
Check whether the returning DataFrame is empty. Raise Exception if df is empty.
Download data from the given set of tickers.
Check whether the returning DataFrame is empty. Raise Exception if df is empty.
Raises Exception when there is an error downloading data.
"""
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

closing_prices_pct = closing_prices.pct_change()
returns = (1 + closing_prices_pct).cumprod() - 1

"""
Calculate returns for the different time periods.
Create main DataFrame to store the following values:
    - Tickers/Symbol
    - Return per period
    - Percentile score per period
    - HQM Score
Calculate the percentile score for a given stock in a given time period.
Calculate the HQM score by getting the average percentile value.
"""

# Define time periods for momentum calculation
time_periods = ['1M return', '3M return', '6M return', '1Y return']
percentiles = [f'{period} percentile' for period in time_periods]

# Retrieve returns for each period
return_values = calculate_monthly_returns(returns, logger, start_date,
                                          time_periods, monthly_offsets)

# Prepare main watchlist DataFrame
watchlist = pd.DataFrame({
    'Symbol': sp500_underlyings['Symbol'],
    **{period: return_values.get(period, pd.Series(dtype='float64'))
        for period in time_periods},
    **{percentile: None for percentile in percentiles},
    'HQM Score': None
}).fillna(0)

# Calculate percentiles and HQM score
yf_tools.calculate_percentiles(watchlist, time_periods, percentiles)
calculate_hqm_score(watchlist, percentiles)

"""
Merge last closing price.
Allocate the number of shares to buy given portfolio size
Sort by HQM score
"""
# Merge closing prices and allocate shares
last_close = closing_prices.iloc[-1].reset_index()
last_close.columns = ['Symbol', 'Close Price']
watchlist = watchlist.merge(last_close, how='inner', on='Symbol')

yf_tools.allocate_shares(watchlist, portfolio_size,
                         'Close Price', 'Num_shares_to_buy')

# Sort by HQM Score and select top 50
watchlist.sort_values('HQM Score', ascending=False, inplace=True)
top_50_momentum = watchlist.head(50).reset_index(drop=True)

top_50_momentum.to_csv('momentum_strategy.csv')
