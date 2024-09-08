"""
This file aims to compare missing RICS (Reuters underlying ticker) on a given platform.
It opens two different files containing RICS data, extract RICS and check whether a RICS is missing.
Create a new file containing missing RICS.
"""
import pathlib
import pandas as pd
import xml.etree.ElementTree as ET

# Define path
file_path = pathlib.Path(r'C:\Users\xxx')

# Define file paths
stock_eqf_path = file_path.joinpath('stocks_eqf.xml')
slv_sets_path = file_path.joinpath('slv_sets.txt')
rics_path = file_path.joinpath('rics_ederivatives.csv')

# Read the CSV file into a DataFrame
rics_edderiv = pd.read_csv(rics_path, delimiter=';')
rics_tickers = rics_edderiv['Security'].to_list()

# Parse the XML file using ElementTree
stock_eqf_tickers = set()
try:
    tree = ET.parse(stock_eqf_path)
    root = tree.getroot()
    # Extract tickers from <mx2> and <mx3> tags
    for underlying in root.findall('.//underlying'):
        for tag in ['mx2', 'mx3']:
            ticker = underlying.find(f'ns0:{tag}', root.nsmap)
            if ticker is not None:
                stock_eqf_tickers.add(ticker.text.strip())
except (ET.ParseError, FileNotFoundError) as e:
    print(f"Error reading XML file: {e}")

# Extract tickers from the slv_sets.txt file
slv_sets_tickers = set()
try:
    with slv_sets_path.open() as file:
        lines = file.readlines()[4:]  # Skip header
        slv_sets_tickers = {line.split('|')[2].strip() for line in lines}
except FileNotFoundError as e:
    print(f"Error reading slv_sets.txt file: {e}")

# Output for debugging purposes
print(f"Stock EQF Tickers: {stock_eqf_tickers}")
print(f"SLV Sets Tickers: {slv_sets_tickers}")

# Define missing RICS
missing_rics_stock_eqf = [rics for rics in rics_tickers if rics not in stock_eqf_tickers]
missing_rics_slv_set = [rics for rics in rics_tickers if rics not in slv_sets_tickers]

# Create dataframe and CSV file containing missing RICS
out_df = pd.DataFrame({'Stock EQF': pd.Series(missing_rics_stock_eqf),
                       'SLV set': pd.Series(missing_rics_slv_set)})
out_df.to_csv(file_path.joinpath('request_overview.csv'), index=False)