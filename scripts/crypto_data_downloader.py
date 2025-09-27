#!/usr/bin/env python3
"""
Interactive Cryptocurrency Data Downloader
Downloads OHLCV data from CoinAPI and saves in CSV format
"""

import requests
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CoinAPI configuration from environment variables
API_KEY = os.getenv('COINAPI_KEY')
BASE_URL = os.getenv('COINAPI_BASE_URL', 'https://rest.coinapi.io/v1')
DATA_FOLDER = os.getenv('DATA_FOLDER', 'data')

# Validate API key
if not API_KEY or API_KEY == 'your_coinapi_key_here':
    print("❌ Error: COINAPI_KEY not found or not set!")
    print("Please:")
    print("1. Copy .env.template to .env")
    print("2. Edit .env and add your CoinAPI key")
    print("3. Get your key from: https://www.coinapi.io/")
    sys.exit(1)

HEADERS = {'X-CoinAPI-Key': API_KEY}

def print_header():
    """Print script header"""
    print("=" * 60)
    print("    🚀 Cryptocurrency Data Downloader")
    print("=" * 60)
    print()

def get_trading_pair():
    """Get trading pair from user input"""
    print("📈 TRADING PAIR SELECTION")
    print("-" * 30)
    print("Examples:")
    print("  • BINANCE_SPOT_BTC_USDT")
    print("  • BINANCE_SPOT_ETH_USDT") 
    print("  • COINBASE_SPOT_BTC_USD")
    print("  • KRAKEN_SPOT_ETH_USD")
    print("  • BINANCE_SPOT_ADA_USDT")
    print()
    
    while True:
        pair = input("Enter trading pair: ").strip().upper()
        if pair:
            return pair
        print("❌ Please enter a valid trading pair!")

def get_resolution():
    """Get candle resolution from user input"""
    print("\n⏰ CANDLE RESOLUTION SELECTION")
    print("-" * 35)
    print("Available resolutions:")
    print("  Seconds: 1SEC, 5SEC, 10SEC, 15SEC, 30SEC")
    print("  Minutes: 1MIN, 5MIN, 15MIN, 30MIN")
    print("  Hours:   1HRS, 4HRS, 6HRS, 12HRS")
    print("  Days:    1DAY, 3DAY, 7DAY")
    print("  Months:  1MTH")
    print()
    print("Examples: 5MIN, 1HRS, 1DAY")
    print()
    
    while True:
        resolution = input("Enter resolution: ").strip().upper()
        if resolution:
            return resolution
        print("❌ Please enter a valid resolution!")

def get_data_range():
    """Get data range from user input"""
    print("\n📅 DATA RANGE SELECTION")
    print("-" * 25)
    print("How much historical data do you want?")
    print("Examples: 100 (last 100 candles), 1000, 5000")
    print()
    
    while True:
        try:
            limit = int(input("Enter number of candles: ").strip())
            if limit > 0:
                return limit
            print("❌ Please enter a positive number!")
        except ValueError:
            print("❌ Please enter a valid number!")

def fetch_data_with_progress(symbol, period_id, limit):
    """Fetch data from CoinAPI with progress tracking"""
    url = f'{BASE_URL}/ohlcv/{symbol}/history'
    params = {
        'period_id': period_id,
        'limit': limit
    }
    
    print(f"\n🔄 Fetching {limit} candles for {symbol} ({period_id})...")
    print(f"📡 API URL: {url}")
    
    # Create progress bar
    with tqdm(total=100, desc="Downloading", unit="%") as pbar:
        # Simulate progress steps
        pbar.update(10)
        time.sleep(0.5)
        
        # Make API request
        response = requests.get(url, headers=HEADERS, params=params)
        pbar.update(50)
        
        if response.status_code != 200:
            pbar.close()
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        pbar.update(30)
        
        # Parse JSON
        data = response.json()
        pbar.update(10)
        
        if not data:
            pbar.close()
            print("❌ No data received from API")
            return None
    
    print(f"✅ Successfully fetched {len(data)} candles")
    return data

def process_data(raw_data):
    """Process raw API data into required CSV format"""
    print("\n🔄 Processing data...")
    
    df = pd.DataFrame(raw_data)
    
    # Convert timestamp
    df['time'] = pd.to_datetime(df['time_period_start'])
    
    # Rename columns to match required format
    processed_df = pd.DataFrame({
        'time': df['time'],
        'open': df['price_open'],
        'high': df['price_high'], 
        'low': df['price_low'],
        'close': df['price_close'],
        'volume': df['volume_traded'],
        'buy_volume': df['volume_traded'] * 0.55,  # Estimate (CoinAPI doesn't provide buy/sell split)
        'sell_volume': df['volume_traded'] * 0.45   # Estimate
    })
    
    # Sort by time (oldest first)
    processed_df = processed_df.sort_values('time')
    
    print(f"✅ Processed {len(processed_df)} records")
    return processed_df

def save_to_csv(df, symbol, period_id):
    """Save DataFrame to CSV file"""
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{period_id}_{timestamp}.csv"
    filepath = os.path.join(DATA_FOLDER, filename)
    
    # Ensure data directory exists
    os.makedirs(DATA_FOLDER, exist_ok=True)
    
    print(f"\n💾 Saving data to: {filepath}")
    
    # Save with progress
    with tqdm(total=100, desc="Saving CSV", unit="%") as pbar:
        df.to_csv(filepath, index=False)
        pbar.update(100)
    
    print(f"✅ Data saved successfully!")
    print(f"📁 File: {filepath}")
    print(f"📊 Records: {len(df)}")
    
    # Show sample data
    print(f"\n📋 Sample data (first 3 rows):")
    print(df.head(3).to_string(index=False))
    
    return filepath

def main():
    """Main function"""
    try:
        print_header()
        
        # Get user inputs
        symbol = get_trading_pair()
        period_id = get_resolution()
        limit = get_data_range()
        
        # Fetch data
        raw_data = fetch_data_with_progress(symbol, period_id, limit)
        if raw_data is None:
            sys.exit(1)
        
        # Process data
        df = process_data(raw_data)
        
        # Save to CSV
        filepath = save_to_csv(df, symbol, period_id)
        
        print(f"\n🎉 Download completed successfully!")
        print(f"📂 Data saved to: {filepath}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
