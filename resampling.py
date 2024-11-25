import pathlib
import pandas as pd

data = pathlib.Path(r'C:\Users\juann\OneDrive\Documentos\GitHub\Finance\Trading - Strategies\data\msft_2022.csv')
df = pd.read_csv(data)
df.columns = df.columns.str.capitalize()

df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Resampling the data into 5-minute intervals
resampled_df = df.resample('5min').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
})