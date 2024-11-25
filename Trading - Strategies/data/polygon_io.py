import pathlib
import pandas as pd

path = pathlib.Path(r'C:\Users\juann\Documents\Datasets')
symbol = 'NFLX_30_minute_2020_05_04_2021_11_20'
full_path = path.joinpath(symbol).with_suffix('.csv')
df = pd.read_csv(full_path, delimiter=';', parse_dates=['Timestamp'],
                 date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S'))
df.columns = df.columns.str.capitalize()
df.set_index('Timestamp', inplace=True)


# # # Resampling the data into 5-minute intervals
out_df = df
# out_df = df.resample('30min').agg({
#         'Volume': 'sum',
#         'Open': 'first',
#         'Close': 'last',
#         'High': 'max',
#         'Low': 'min',
#         'Num_trans': 'sum'
#     }).dropna()

# 25, 50

# """
# AMD
# DIS
# ACN
# ORCL
# UPS
# SBUX
# AVGO
# ARM
# TMUS
# VZ
# CMCSA
# BSX
# DVA
# HCA
# RMD
# LLY
# NKE
# BAC
# NFLX
# META

# """