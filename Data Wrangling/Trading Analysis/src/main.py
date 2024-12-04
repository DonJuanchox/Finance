"""
This file aims toidentify any breaks between the ‘Trading Positions’
and the ‘Clearing Positions’ 
"""
import etl_tools as etl
from etl_logger import get_logger
import pathlib
import pandas as pd
import tools
import logging
import typing


"""
Set up logger.
Extract data from the folder.
Load data using pandas.
FX_file only contains two rows, it is possible to load the data without pandas
"""
# Set up logger
logger = get_logger('Logg', logging.WARNING, [logging.StreamHandler()])

# Extract
file_folder = pathlib.Path(
    r'C:\Users\juann\OneDrive\Documentos\GitHub\OOP\Trading Analysis')
trading_file = file_folder.joinpath('trading_data.csv')
clearing_file = file_folder.joinpath('clearing_data.csv')
fx_file = file_folder.joinpath('fx_rate.csv')

# Load
trading_df: pd.DataFrame = etl.load_csv(trading_file, parse_dates=True)\
    .rename(columns={'net_position': 'net_position_trading'})
clearing_df: pd.DataFrame = etl.load_csv(clearing_file, parse_dates=True)\
    .rename(columns={'net_position': 'net_position_clearing'})
fx_rate_df: pd.DataFrame = etl.load_csv(fx_file)

"""
Data Wrangle:
    - Convert Fx_rate dataframe into a dictionary
    - Create an unique id to identify each trade
    - Merge data to compare trading vs clearing
    - Sum net_positions as there might be trades having
    similar values but different net position
    - Get the fx_rate value for a given currency
"""
# Dictionary -> {fx_pair:eur_rate}
fx_rate_df.set_index('ccy_pair', inplace=True)
fx_rate: typing.Dict = fx_rate_df['rate'].to_dict()

# Id per trade
trading_df['main_id'] = trading_df\
    .apply(lambda row: tools.generate_id(row, ['symbol', 'product_type', 'put_call', 'strike',
                                               'maturity_date']), axis=1)
clearing_df['main_id'] = clearing_df\
    .apply(lambda row: tools.generate_id(row, ['symbol', 'product_type', 'put_call', 'strike',
                                               'maturity_date']), axis=1)

# Merge data --> need to fix the fillna(0)
out_df = trading_df.merge(clearing_df[['main_id', 'net_position_clearing']],
                          how='left', on='main_id')
# Groupby and pipeline
out_df = out_df.fillna(0).groupby(by=['symbol', 'product_type', 'put_call',
                                      'strike', 'maturity_date', 'price',
                                      'main_id', 'multiplier', 'currency'],
                                  as_index=False)\
    .agg({'net_position_clearing': 'sum',
          'net_position_trading': 'sum'})\
    .assign(break_pos= lambda df:
            df['net_position_clearing'] - df['net_position_trading'])\
    .loc[lambda x: x['break_pos'] != 0].sort_values(by=['symbol'])\
    .assign(fx_eur_rate=lambda df:
            df.apply(lambda row:
                     tools.get_rate(logger, fx_rate, row['currency']), axis=1))\
    .assign(break_in_eur=lambda df:
            round((df['fx_eur_rate'] * df['break_pos']), 2))\
    .filter(items=['symbol', 'product_type', 'put_call', 'strike',
                   'maturity_date', 'net_position_clearing',
                   'net_position_trading', 'break_in_eur'])

out_df.to_csv('breaking_position.csv')
