"""
This file aims to incorporate Sector value to a given set of underlyings, 
by extracting the information from Bloomberg API
and return companies with missing logo.
"""

import pandas as pd
import pathlib
from xbbg import blp
import json

# Define path
bbg_sector = "GICS_SECTOR_NAME"
file_path = pathlib.Path('C:/Users/xxx')
assetConfig = file_path.joinpath('assetConfig.txt')
market_logos = file_path.joinpath('market-logos.txt')

with open(assetConfig, "r") as file_1, open(market_logos, "r") as file_2:
    # Load data
    company_data = json.load(file_1)
    logos = json.load(file_2)
    
    # Close files
    file_1.close()
    file_2.close()
    
    # Get missing logos
    companies_logos = [asset['underlying'] for asset in logos]
    all_tickers = list(company_data.keys())
    missing_logos = [company for company in all_tickers if company not in companies_logos]

    # Request data from Bloomberg
    tickers = set(item['BBGOptionRic'] + ' ' + item['BBGAssetType']
                  for key, item in company_data.items())
    sector = blp.bdp(tickers,flds=[bbg_sector]).reset_index(drop=False, names=['ticker'])
    
    # Incorporate sector values
    for key, values in company_data.items():
        temporary_ticker = values['BBGOptionRic'] + ' ' + values['BBGAssetType']
        if temporary_ticker in sector.ticker.values:
            company_data[key]['AutomaticUploadFwdfit'] = False
            company_data[key]['AutomaticUploadVolfit'] = False
            company_data[key]['Sector'] = sector[sector['ticker'] == temporary_ticker]['gics_sector_name'].item()

with open(f'{file_path}\\{file_1}.txt', "w", encoding="utf-8") as file_1, open(f'{file_path}\\Missing_Logos.txt', "w", encoding="utf-8") as file_2:
    file_1.write(json.dump(company_data, ensure_ascii=False, indent=4, sort_keys=True))
    file_2.write(json.dump(missing_logos, ensure_ascii=False, indent=4, sort_keys=True))
    file_1.close()
    file_2.close()