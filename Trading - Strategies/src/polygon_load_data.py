import pathlib
import pandas as pd

# Define the dataset path and file
DATA_DIR = pathlib.Path(r'C:\Users\juann\Documents\Datasets')
SYMBOL = 'NFLX_30_minute_2020_05_04_2021_11_20'
FILE_EXTENSION = '.csv'

# Construct full file path
full_path = DATA_DIR.joinpath(SYMBOL).with_suffix(FILE_EXTENSION)

# Validate file existence
if not full_path.exists():
    raise FileNotFoundError(f"The file {full_path} does not exist.")

# Load the dataset
try:
    df = pd.read_csv(
        full_path,
        delimiter=';',  # Adjust delimiter if necessary
        parse_dates=['Timestamp'],  # Parse the Timestamp column as datetime
        date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S')
    )
except Exception as e:
    raise ValueError(f"Error reading the file: {e}")

# Capitalize column names for consistency
df.columns = df.columns.str.capitalize()

# Set Timestamp as the index
if 'Timestamp' not in df.columns:
    raise KeyError("The dataset must contain a 'Timestamp' column for time indexing.")
df.set_index('Timestamp', inplace=True)

# Print basic dataset info
print(f"Dataset loaded successfully with {len(df)} rows.")
print(df.info())

# Resample Data Function
def resample_data(dataframe, interval='5T'):
    """
    Resamples the given dataframe to a specified time interval.
    
    Args:
        dataframe (pd.DataFrame): Original dataframe with a datetime index.
        interval (str): Resampling interval (e.g., '5T' for 5 minutes, '30T' for 30 minutes).
    
    Returns:
        pd.DataFrame: Resampled dataframe.
    """
    return dataframe.resample(interval).agg({
        'Volume': 'sum',
        'Open': 'first',
        'Close': 'last',
        'High': 'max',
        'Low': 'min',
        'Num_trans': 'sum'
    }).dropna()

# Optionally resample the data
try:
    RESAMPLE_INTERVAL = '30t'  # Change to desired interval (e.g., '5T' for 5 minutes)
    out_df = resample_data(df, interval=RESAMPLE_INTERVAL)
    print(f"Data resampled to {RESAMPLE_INTERVAL} intervals.")
except KeyError as e:
    raise KeyError(f"One or more required columns for resampling are missing: {e}")
except Exception as e:
    raise ValueError(f"An error occurred during resampling: {e}")
