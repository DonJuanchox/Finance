import requests
import pandas as pd
from datetime import datetime, timedelta
import pathlib

# Replace with your actual Polygon.io API key
API_KEY = ""

# List of stocks
STOCKS = [
"AMD",
"DIS",
"ACN",
"ORCL",
"UPS",
"SBUX",
"AVGO",
"ARM",
"TMUS",
"VZ",
"CMCSA",
"BSX",
"DVA",
"HCA",
"RMD",
"LLY",
"NKE",
"BAC",
"NFLX",
"META",
]

# Output directory
DATASET_PATH = pathlib.Path(r'C:\Users\juann\Documents\Datasets')

# Parameters
START_DATE = datetime(2020, 5, 4)
END_DATE = datetime(2021, 11, 20)
INTERVAL_DESC = "minute"
INTERVAL_TIME = 30
LIMIT = 50000
CHUNK_DAYS = 7  # Number of days per chunk for API requests


def transform_date(timestamp):
    """Convert a timestamp to a datetime object."""
    return datetime.utcfromtimestamp(timestamp / 1000.0)


def fetch_data(symbol, start_date, end_date, interval_time, interval_desc, limit, api_key):
    """
    Fetch data for a given stock symbol and date range.
    """
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    base_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{interval_time}/{interval_desc}/{from_date}/{to_date}"
    
    try:
        response = requests.get(base_url, params={"apiKey": api_key, "limit": limit})
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return []


def process_data(data):
    """
    Convert raw data into a DataFrame with appropriate transformations.
    """
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df.columns = ['Volume', 'Weighted Volume', 'Open', 'Close', 'High', 'Low', 'Timestamp', 'Num_trans']
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms', utc=True)
    df['Timestamp'] = df['Timestamp'].dt.tz_convert('US/Eastern')
    df = df[
        (df['Timestamp'].dt.time >= pd.to_datetime("09:30").time()) &
        (df['Timestamp'].dt.time <= pd.to_datetime("16:00").time())
    ]
    df['Timestamp'] = df['Timestamp'].dt.tz_localize(None)
    return df


def save_data(df, symbol, interval_time, interval_desc, start_date, end_date, output_path):
    """
    Save processed DataFrame to a CSV file.
    """
    if df.empty:
        print(f"No data to save for {symbol}.")
        return
    
    file_name = f"{symbol}_{interval_time}_{interval_desc}_{start_date:%Y_%m_%d}_{end_date:%Y_%m_%d}.csv"
    file_path = output_path.joinpath(file_name)
    df.to_csv(file_path, index=False, sep=';')
    
    
    print(f"Data saved to {file_path}")


def fetch_and_save_stock_data(symbol, start_date, end_date, interval_time, interval_desc, limit, api_key, output_path):
    """
    Fetch, process, and save stock data for a given symbol.
    """
    all_data = []
    current_start = start_date

    while current_start < end_date:
        current_end = current_start + timedelta(days=CHUNK_DAYS)
        if current_end > end_date:
            current_end = end_date

        print(f"Fetching data for {symbol} from {current_start} to {current_end}")
        data = fetch_data(symbol, current_start, current_end, interval_time, interval_desc, limit, api_key)
        all_data.extend(data)
        current_start = current_end + timedelta(days=1)

    df = process_data(all_data)
    save_data(df, symbol, interval_time, interval_desc, start_date, end_date, output_path)


def main():
    """
    Main function to fetch and save data for all stocks.
    """
    for symbol in STOCKS:
        print(f"Processing stock: {symbol}")
        fetch_and_save_stock_data(
            symbol, START_DATE, END_DATE, INTERVAL_TIME, INTERVAL_DESC, LIMIT, API_KEY, DATASET_PATH
        )
    print("All data fetching and saving complete.")


if __name__ == "__main__":
    main()
