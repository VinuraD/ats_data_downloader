import requests
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timedelta

headers = {'X-CoinAPI-Key': 'a2fce816-4100-470b-9e50-64e0962eda50'}
symbol = 'BINANCE_SPOT_BTC_USDT'
url = f'https://rest.coinapi.io/v1/ohlcv/{symbol}/history?period_id=1DAY&limit=14'

print("Fetching data from CoinAPI...")
r = requests.get(url, headers=headers)

if r.status_code == 200:
    print("API request successful!")
    data = r.json()
    df = pd.DataFrame(data)
    df['time_period_start'] = pd.to_datetime(df['time_period_start'])
    df.set_index('time_period_start', inplace=True)

    df.rename(columns={
        'price_open': 'Open',
        'price_high': 'High',
        'price_low': 'Low',
        'price_close': 'Close',
        'volume_traded': 'Volume'
    }, inplace=True)
else:
    print(f"API request failed with status code: {r.status_code}")
    print(f"Error: {r.text}")
    print("Using sample data instead...")
    
    # Create sample BTC data for demonstration
    dates = pd.date_range(start=datetime.now() - timedelta(days=13), periods=14, freq='D')
    sample_data = {
        'Open': [65000, 65200, 64800, 66000, 65500, 67000, 66800, 68000, 67500, 69000, 68200, 70000, 69500, 71000],
        'High': [65500, 65800, 65200, 66500, 66000, 67500, 67200, 68500, 68000, 69500, 68700, 70500, 70000, 71500],
        'Low': [64500, 64800, 64300, 65500, 65000, 66500, 66300, 67500, 67000, 68500, 67800, 69500, 69000, 70500],
        'Close': [65200, 64800, 66000, 65500, 67000, 66800, 68000, 67500, 69000, 68200, 70000, 69500, 71000, 70800],
        'Volume': [1000, 1200, 800, 1500, 900, 1800, 1100, 2000, 1300, 1600, 1400, 2200, 1700, 1900]
    }
    df = pd.DataFrame(sample_data, index=dates)

print("Data loaded successfully!")
print(df.head())
print(f"Data shape: {df.shape}")

mpf.plot(df, type='candle', title='BTC/USDT', volume=True)