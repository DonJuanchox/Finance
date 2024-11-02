import pandas as pd
import math
from scipy import stats
import yfinance as yf
from typing import Union, List
import warnings

# Suppress warnings for pandas operations
warnings.filterwarnings('ignore')


def get_sp500_tickers() -> pd.DataFrame:
    """
    Retrieve a DataFrame containing data on companies listed in the S&P 500 from Wikipedia.

    The DataFrame includes the following columns:
        - Symbol: Ticker symbol of the company, formatted for Yahoo Finance.
        - Security: Name of the company.
        - GICS Sector: Sector classification under the Global Industry Classification Standard.
        - GICS Sub-Industry: More specific industry classification.
        - Headquarters Location: City and state of company headquarters.
        - Date Added: Date the company was added to the S&P 500 index.
        - CIK: Central Index Key assigned by the SEC.
        - Founded: Year the company was founded.

    Returns
    -------
    pd.DataFrame
        DataFrame containing S&P 500 companies data, sorted alphabetically by Symbol.

    Notes
    -----
    The 'Symbol' column is adjusted to replace '.' with '-' to match Yahoo Finance conventions.
    """
    wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp500_df = pd.read_html(wiki_url)[0]
    sp500_df['Symbol'] = sp500_df['Symbol'].str.replace('.', '-')
    return sp500_df.sort_values("Symbol").reset_index(drop=True)


def allocate_shares(df: pd.DataFrame,
                    portfolio_size: Union[int, float],
                    price_column: str,
                    shares_column: str) -> pd.DataFrame:
    """
    Allocate the number of shares to purchase for each stock based on a specified portfolio size.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing stock price data.
    portfolio_size : Union[int, float]
        Total amount allocated to the portfolio, e.g., 10_000_000.
    price_column : str
        Column in the DataFrame with the stock prices.
    shares_column : str
        Column name where the calculated number of shares to buy will be stored.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with an added column showing the allocated number of shares per stock.

    Notes
    -----
    This function rounds down to the nearest whole number of shares for each stock.
    """
    df[shares_column] = df[price_column].apply(lambda x: math.floor(
        portfolio_size / x) if not math.isnan(x) else None)
    return df


def calculate_percentiles(df: pd.DataFrame,
                          target_columns: List[str],
                          percentile_columns: List[str]) -> pd.DataFrame:
    """
    Calculate and assign percentiles for specific columns in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing numerical data for percentile calculations.
    target_columns : List[str]
        List of column names to calculate percentiles for.
    percentile_columns : List[str]
        List of column names to store the resulting percentiles.

    Returns
    -------
    pd.DataFrame
        DataFrame with additional columns containing percentile ranks for each target column.

    Notes
    -----
    Each percentile is calculated as the percentage rank of a value relative to the other values
    in its column, scaled to a range of 0 to 1.
    """
    for target, percentile in zip(target_columns, percentile_columns):
        df[percentile] = df[target].apply(
            lambda x: stats.percentileofscore(df[target], x) / 100)
    return df


def get_ticker_info(tickers: List[str], info_values: List[str]) -> pd.DataFrame:
    """
    Retrieve specific information fields for a list of stock tickers.

    Parameters
    ----------
    tickers : List[str]
        List of stock ticker symbols.
    info_values : List[str]
        List of specific information fields to retrieve for each ticker, such as "sector", "marketCap".

    Returns
    -------
    pd.DataFrame
        DataFrame with each row representing a ticker and each column containing requested information.

    Notes
    -----
    If information for a ticker is unavailable, the respective row will contain `None` for the missing fields.
    Any errors encountered while fetching data will be reported, and the ticker will return `None` for all fields.
    """
    stock_data = yf.Tickers(" ".join(tickers))
    ticker_info = {}

    for ticker in tickers:
        try:
            info = stock_data.tickers[ticker].info
            sub_dict = {key: info.get(key)
                        for key in info_values if key in info}
            ticker_info[ticker] = sub_dict if sub_dict else None
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            ticker_info[ticker] = None

    return pd.DataFrame(ticker_info).T


def get_financial_statements(tickers: List[str], statements: List[str]) -> pd.DataFrame:
    """
    Retrieve specified financial statement items for a list of stock tickers.

    Parameters
    ----------
    tickers : List[str]
        List of stock ticker symbols.
    statements : List[str]
        List of financial statement items to retrieve, such as "totalRevenue", "grossProfit".

    Returns
    -------
    pd.DataFrame
        DataFrame with each row representing a ticker and columns containing the requested financial data.

    Notes
    -----
    If financial statement data is unavailable for a ticker, `None` will be recorded for that ticker.
    Any errors encountered while fetching data will be reported, and the respective ticker will return `None` for all requested items.
    """
    stock_data = yf.Tickers(" ".join(tickers))
    financial_data = {}

    for ticker in tickers:
        try:
            financials = stock_data.tickers[ticker].financials
            if not financials.empty:
                last_data = financials.iloc[:, 0]
                data = last_data.filter(items=statements).to_dict()
                financial_data[ticker] = data if data else None
            else:
                financial_data[ticker] = None
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            financial_data[ticker] = None

    return pd.DataFrame(financial_data).T
