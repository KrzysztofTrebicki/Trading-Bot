# Imports
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import seaborn as sns

# Read parquet dataframe
def get_df():
    # Read_parquet
    df = pd.read_parquet('raw_data.parquet', engine='pyarrow')
    # Choose columns
    cols = ['time', 'close']
    df = df[cols]
    
    return df

# Add SMA columns
def calculate_SMA(df, SMA_short, SMA_long):
    # Add columns for SMA strategy
    df['SMA_short'] = ta.sma(df['close'],SMA_short)
    df['SMA_long'] = ta.sma(df['close'],SMA_long)
    # Delete rows with NaN values for SMA columns 
    df = df.dropna().reset_index(drop=True)
    
    return df

# Extract date from the timestamp and add as a separate column
def extract_date(df):
    # Extract date from the timestamp
    date_column = df['time'].dt.date
    # Add date column
    df.insert(loc=1, column='date', value=date_column)
    
    return df

# Add columns with the closing price in the moment when the BUY or SELL action occur
def add_trade_signals(df):
    # Create columns with BUY and SELL signals
    buy_condition = (df['SMA_short'] >= df['SMA_long']) & (df['SMA_short'].shift(1) < df['SMA_long'].shift(1))
    sell_condition = (df['SMA_short'] < df['SMA_long']) & (df['SMA_short'].shift(1) >= df['SMA_long'].shift(1))
    # Add columns
    df['signals_buy'] = df.loc[buy_condition, 'close']
    df['signals_sell'] = df.loc[sell_condition, 'close']

    return df

# Prepare data for SMA strategy
def SMA_data(df, SMA_short, SMA_long):
    # Add SMA columns
    df = calculate_SMA(df, SMA_short, SMA_long)
    # Add columns for BUY/SELL signals
    df = add_trade_signals(df)
    
    return df

# Plot with of closing prices with BUY/SELL signals marked
def plot_SMA(df,SMA_short, SMA_long, start_date, end_date):  # both dates need to be entered in a yyyy-mm-dd format
    # Add date column
    df = extract_date(df)
    # Filter data by date
    df = df.loc[(df['date'] >= pd.to_datetime(start_date).date()) & (df['date'] <= pd.to_datetime(end_date).date())]
    # Prepare data w SMA strategy
    df = SMA_data(df, SMA_short, SMA_long)
    # Plot SMAs and BUY/SELL signals
    fig, ax = plt.subplots(figsize=(26,12))
    ax.plot(df['time'], df['close'], label = 'BTC/BUSD' ,linewidth=1 ,color='blue', alpha = 0.9)
    ax.plot(df['time'], df['SMA_short'], label = f'SMA{SMA_short}', linewidth=1, alpha = 0.85)
    ax.plot(df['time'], df['SMA_long'], label = f'SMA{SMA_long}', linewidth=1,  alpha = 0.85)
    ax.scatter(df['time'], df['signals_buy'] , label = 'Buy' , marker = '^', color = 'green', alpha=1, linewidths=5)
    ax.scatter(df['time'], df['signals_sell'] , label = 'Sell' , marker = 'v', color = 'red', alpha=1, linewidths=5)
    ax.set_title(f'BTC/BUSD - Price History with buy and sell signals ({start_date} - {end_date})',fontsize=20)
    ax.set_xlabel('Time' ,fontsize=18)
    ax.set_ylabel('Close Price INR (₨)' , fontsize=18)
    ax.legend()
    ax.grid()
    plt.tight_layout()
    plt.show()
    
# Create evaluation metrics for differnt lengths of SMAs
def evaluate_signals(df):
    # Drop null values from 
    signals_buy = df["signals_buy"].dropna()
    signals_sell = df["signals_sell"].dropna()
    # Create multipliers list
    multipliers_list = []
    # Append to multiplier list in chronogical manner
    for s, b in zip(signals_sell, signals_buy):
        multiplier = s / b
        multipliers_list.append(multiplier)
    # Convert to pd.Series
    multipliers = pd.Series(multipliers_list, index = range(len(multipliers_list)))
    # Take last observation as overall profit multiplier
    overall_profit_multiplier = multipliers.cumprod().iloc[-1]
    
    # Return evaluation metrics
    return {
        "average_profit_multiplier": signals_sell.mean() / signals_buy.mean(),
        "buy_sell_trade_pair_count": (signals_buy.count() + signals_sell.count()) / 2,
        "overall_profit_multiplier": overall_profit_multiplier
    }

# Evaluate combinations of SMAs lengths   
df_raw = get_df()

def evaluate_sma_combination(sma_pair):
    # Unpack SMAs
    sma_short, sma_long = sma_pair
    # Process data 
    df = add_trade_signals(calculate_SMA(df_raw, sma_short, sma_long))
    # Instantiate dictionary
    result = {
        "SMA_short": sma_short,
        "SMA_long": sma_long
    }
    # Populate dictionary with evaluation metrics
    result.update(evaluate_signals(df))
    
    return result

# Plot heatmaps with evaluation metrics for SMA lengths
def heatmaps_SMA(df, symbol):
    # Create dictionary for evaluation metrics
    cols = [
        "average_profit_multiplier",
        "buy_sell_trade_pair_count",
        "overall_profit_multiplier"
    ]
    # Plot figure
    fig, axes = plt.subplots(1, len(cols), figsize=(26, 5))
    fig.suptitle(symbol)
    # Loop for metrics
    for i, col in enumerate(cols):
        matrix = df.pivot(index='SMA_long', columns='SMA_short', values=col)         
        sns.heatmap(matrix, cbar=True, square=True, cmap="viridis", ax=axes[i]).invert_yaxis()
        axes[i].set_title(col)


