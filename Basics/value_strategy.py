"""
Module aims to develop a value strategy to analyze stocks.

Using the S&P500 underlyings in order to analyze their financial statements.
Score underlyings under RV Score which represents xxx.
Current drawback this module experience is the lack of last available financial
statements for the given underlyings.
"""
import pandas as pd
import yfinance as yf
import datetime as dt
import warnings
from typing import List

import yf_tools
warnings.filterwarnings('ignore')  # Suppress warnings for pandas operations


def calculate_rv_score(df: pd.DataFrame,
                       percentile_cols: List[str]) -> pd.DataFrame:
    """
    Compute and assigns RV score based on specified percentiles.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing financial data.
    percentile_cols : List[str]
        DataFrame columns which store percile values for a given underlying.

    Returns
    -------
    df : pd.DataFrame
        Original DataFrame containing HQM score.

    """
    df['RV score'] = df[percentile_cols].mean(axis=1)
    return df


"""
Get data & define variables:
    - Get S&P500 tickers
    - Retrieve data for last available data
    - Define percentile & ratio columns
    - Retrive financial statement data
    - Retrive underlying information
"""
# Get ticker symbols
underlyings = yf_tools.get_sp500_tickers()

# Fetch recent prices
yesterday = dt.date.today() - dt.timedelta(days=2)
last_close = yf.download(underlyings.Symbol.to_list(),
                         start=yesterday)['Close'].iloc[-1].reset_index()
last_close.columns = ['Symbol', 'Price']

# Define variables
portfolio_size: int = 10_000_000  # Portfolio size in dollars
percentile_cols = ['PE Percentile', 'PB Percentile', 'PS Percentile',
                   'EV/EBITDA Percentile', 'EV/Gross Profit Percentile']
ratio_cols = ['trailingPE', 'priceToBook',
              'priceToSalesTrailing12Months', 'EV/EBITDA', 'EV/Gross Profit']

# Retrieve financial data and ratios
financials_df = yf_tools.get_financial_statements(underlyings.Symbol.to_list(),
                                                  ['Gross Profit', 'EBITDA'])\
    .reset_index(names='Symbol')
ratios_df = yf_tools.get_ticker_info(underlyings.Symbol.to_list(),
                                     ['trailingPE', 'enterpriseValue',
                                      'bookValue', 'priceToBook', 'ebitda',
                                      'priceToSalesTrailing12Months'])\
    .reset_index(names='Symbol')

"""
Create main DataFrame by merging last closing price,
with financial and ratio DataFrames.
Calculate Ratios.
Calculate Percentiles.
"""
# Merge data
pe_ratio_df = last_close.merge(financials_df, on='Symbol')\
    .merge(ratios_df, on='Symbol').dropna()

# Calculate additional ratios
pe_ratio_df['EV/EBITDA'] = pe_ratio_df['enterpriseValue'] / pe_ratio_df['EBITDA']
pe_ratio_df['EV/Gross Profit'] = pe_ratio_df['enterpriseValue'] / pe_ratio_df['Gross Profit']

# Add percentile columns and calculate percentiles
pe_ratio_df = pd.concat([pe_ratio_df, pd.DataFrame(columns=percentile_cols)])
yf_tools.calculate_percentiles(pe_ratio_df, ratio_cols, percentile_cols)

"""
Calculate RV Score.
Get the top 50 RV Score's underlyings.
Allocate to number of shares to buy given portfolio size.
"""
# Calculate and sort by RV score
calculate_rv_score(pe_ratio_df, percentile_cols)
top_50_rv = pe_ratio_df.sort_values('RV score').head(50).reset_index(drop=True)

# Allocate shares
yf_tools.allocate_shares(top_50_rv, portfolio_size,
                         'Price', 'Num_shares_to_buy')

top_50_rv.to_csv('value_strategy.csv')
