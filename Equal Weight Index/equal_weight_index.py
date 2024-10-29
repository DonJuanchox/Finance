import numpy as np
import pandas as pd
from pandas import DataFrame
import requests
import yfinance as yf
import math
import xlsxwriter
import time
from typing import Optional

import warnings
warnings.filterwarnings('ignore') # ignore warnings specially for pandas

def get_sp500_tickers() -> DataFrame:
    """
    Retrieves the list of S&P 500 companies from Wikipedia.

    This function fetches the latest table of S&P 500 companies from Wikipedia,
    using `pandas.read_html` to read and extract the data. It returns a DataFrame
    containing the full details of the S&P 500 companies, including symbols, 
    company names, and other information provided in the table.

    Returns:
    -------
    DataFrame
        A DataFrame containing data on S&P 500 companies as obtained from Wikipedia.
    """
    wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(wiki_url)
    sp500_df = table[0]
    return sp500_df

def get_market_cap(ticker: str) -> Optional[float]:
    """
    Retrieves the market capitalization for a given stock ticker symbol.

    This function uses the `yfinance` library to access stock data. It introduces
    a delay of 0.5 seconds to respect potential rate limits and fetches the
    market cap for the specified ticker symbol. If market cap information is 
    unavailable or an error occurs, it returns `None`.

    Parameters:
    ----------
    ticker : str
        The stock ticker symbol (e.g., "AAPL" for Apple Inc.).

    Returns:
    -------
    Optional[float]
        The market capitalization of the stock if available, otherwise `None`.
    """
    time.sleep(0.5)  # Introduce a delay of 0.5 seconds to avoid rate limiting
    try:
        stock = yf.Ticker(ticker)
        market_cap = stock.info.get('marketCap')  # Safely access marketCap
        if market_cap:  # Check if market cap data is available
            return float(market_cap)  # Ensures consistent float return type
    except KeyError:
        return None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


# -- Load data
tickers = get_sp500_tickers()\
.assign(Symbol=lambda df:
        df['Symbol'].str.replace('.', '-'))\
.assign(marketCap= lambda df:
        df['Symbol'].apply(lambda row: get_market_cap(row)))\
.assign(num_of_shares_to_buy=None)

# -- Add price to each Symbol
closing_price = yf.download(tickers.Symbol.to_list(), period='1d')['Close'].T
closing_price = closing_price.reset_index()
closing_price = closing_price.rename(columns={closing_price.columns[-1]: 'Price',
                                              'Ticker': 'Symbol'})
tickers = tickers.merge(closing_price, how='inner', on='Symbol')\
.filter(items=['Symbol', 'marketCap', 'num_of_shares_to_buy', 'Price'])

# -- Define portfolio size & calculate shares to buy
portfolio_size = 10000000
position_size = portfolio_size / len(tickers.index)

for idx in range(0, len(tickers.index)):
    tickers.loc[idx, 'num_of_shares_to_buy'] = math.floor(position_size / tickers.loc[idx, 'Price'])

# -- Creating XLSX file
writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
tickers.to_excel(writer, 'Recommended Trades', index=False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
    {
        'font_color': font_color,
        'bg_color': background_color,
        'border_color': 1
    }
)

dollar_format = writer.book.add_format(
    {
        'num_format': '$0.00',
        'font_color': font_color,
        'bg_color': background_color,
        'border_color': 1
    }
)

integer_format = writer.book.add_format(
    {
        'num_format': '0',
        'font_color': font_color,
        'bg_color': background_color,
        'border_color': 1
    }
)

column_formats = {
    'A' : ['Symbol', string_format],
    'B' : ['marketCap', dollar_format],
    'C' : ['Number shares to buy', integer_format],
    'D' : ['Price', dollar_format]
}

for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 18, column_formats[column][1])
writer.close()