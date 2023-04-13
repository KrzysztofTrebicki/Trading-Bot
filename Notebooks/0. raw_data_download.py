from binance.client import Client
import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# Variable for the location of settings.json
import_filepath = "settings.json"


# Import API keys 
def get_project_settings(importFilepath):
    # Test the filepath to sure it exists
    if os.path.exists(importFilepath):
        # Open the file
        f = open(importFilepath, "r")
        # Get the information from file
        project_settings = json.load(f)
        # Close the file
        f.close()
        # Return project settings to program
        return project_settings
    else:
        return ImportError
    
   
   
# Project settings import 
project_settings = get_project_settings(import_filepath)
# Declare the keys
api_key = project_settings['BinanceKeys']['API_Key']
secret_key = project_settings['BinanceKeys']['Secret_Key']
# Pass API keys 
client = Client(api_key, secret_key)


#Instantiate data generator
data_generator = client.get_historical_klines_generator("BTCBUSD", Client.KLINE_INTERVAL_1MINUTE, "1 Jan 2021", "27 Mar 2023") # range needed to obtain values for SMA calculation
# List the output of generator
raw_data = list(data_generator)
# Empty list for 
converted_data = []
# Populate converted_list with cobverted data (in a form of dictionary)
for candle in raw_data:
    # Dictionary object
    converted_candle = {
            'time': candle[0],
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5]),
            'close_time': candle[6],
            'quote_asset_volume': float(candle[7]),
            'number_of_trades': int(candle[8]),
            'taker_buy_base_asset_volume': float(candle[9]),
            'taker_buy_quote_asset_volume': float(candle[10])
    }
    # Add to converted_data
    converted_data.append(converted_candle)
    
    
# Transform rconverted_data into a Pandas DataFrame
df_data = pd.DataFrame(converted_data)
# Convert the time to human readable format (Binance uses micro-seconds)
df_data['time'] = pd.to_datetime(df_data['time'], unit='ms')
# Convert the close time to human readable format (Binance uses micro-seconds)
df_data['close_time'] = pd.to_datetime(df_data['close_time'], unit='ms') 


# Convert DataFrame to Apache Arrow Table
table = pa.Table.from_pandas(df_data)
# Write data as parquet with Brotli compression (most space efficient type of compression)
pq.write_table(table, 'BTC_data_1m_01012021.parquet')

