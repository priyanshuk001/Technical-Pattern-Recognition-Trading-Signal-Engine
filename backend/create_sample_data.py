"""
Generate sample OHLCV data for testing pattern detection
Run this to create test data when Yahoo Finance fails
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_sample_data():
    """Generate realistic sample OHLCV data for Indian stocks"""
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Major Indian stocks to create sample data for
    tickers = [
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 
        'ICICIBANK.NS', 'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS',
        'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS', 'AXISBANK.NS',
        'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS',
        'BAJFINANCE.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS'
    ]
    
    print("=" * 70)
    print("GENERATING SAMPLE OHLCV DATA FOR TESTING")
    print("=" * 70)
    print()
    
    # Generate data for each ticker
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Creating data for {ticker}...")
        
        # 60 days of data (2 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=70)  # Extra days for weekends
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Different base prices for different stocks (realistic ranges)
        if 'TCS' in ticker:
            base_price = np.random.uniform(3800, 4200)
        elif 'INFY' in ticker:
            base_price = np.random.uniform(1400, 1800)
        elif 'RELIANCE' in ticker:
            base_price = np.random.uniform(2800, 3200)
        elif 'HDFCBANK' in ticker or 'ICICIBANK' in ticker:
            base_price = np.random.uniform(1600, 2000)
        elif 'BAJFINANCE' in ticker:
            base_price = np.random.uniform(6500, 7500)
        elif 'TITAN' in ticker:
            base_price = np.random.uniform(3200, 3600)
        elif 'NESTLEIND' in ticker:
            base_price = np.random.uniform(2200, 2600)
        elif 'ULTRACEMCO' in ticker:
            base_price = np.random.uniform(10000, 11000)
        elif 'ASIANPAINT' in ticker:
            base_price = np.random.uniform(2800, 3200)
        else:
            base_price = np.random.uniform(400, 800)
        
        # Simulate realistic price movements
        np.random.seed(i * 42)  # Reproducible but different for each stock
        
        # Create realistic patterns by combining trend + cycles + noise
        trend = np.linspace(0, np.random.uniform(-0.05, 0.10), len(dates))
        cycle = 0.03 * np.sin(np.linspace(0, 4 * np.pi, len(dates)))
        noise = np.random.normal(0, 0.015, len(dates))
        
        returns = trend + cycle + noise
        
        # Generate close prices
        close_prices = base_price * (1 + returns).cumprod()
        
        # Generate OHLC prices with realistic relationships
        daily_volatility = np.random.uniform(0.01, 0.03, len(dates))
        
        open_prices = close_prices * (1 + np.random.uniform(-0.005, 0.005, len(dates)))
        high_prices = close_prices * (1 + daily_volatility * np.random.uniform(0.5, 1.5, len(dates)))
        low_prices = close_prices * (1 - daily_volatility * np.random.uniform(0.5, 1.5, len(dates)))
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'adj close': close_prices
        })
        
        # Ensure OHLC consistency (High >= max(O,C), Low <= min(O,C))
        df['high'] = df[['high', 'open', 'close']].max(axis=1)
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        # Round to 2 decimal places
        for col in ['open', 'high', 'low', 'close', 'adj close']:
            df[col] = df[col].round(2)
        
        # Format date as string
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Save to CSV
        filename = f'data/{ticker}.csv'
        df.to_csv(filename, index=False)
        print(f"    ✓ Saved {filename} ({len(df)} rows, price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f})")
    
    # Also create index data
    print()
    print("Creating index data...")
    indices = [
        ('^NSEI', 'INDEX_^NSEI.csv', 21000, 23000),      # Nifty 50
        ('^BSESN', 'INDEX_^BSESN.csv', 70000, 76000),    # Sensex
        ('^NSEBANK', 'INDEX_^NSEBANK.csv', 48000, 52000), # Bank Nifty
    ]
    
    for ticker, filename, low_range, high_range in indices:
        base_price = np.random.uniform(low_range, high_range)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        
        trend = np.linspace(0, 0.05, len(dates))
        noise = np.random.normal(0, 0.012, len(dates))
        returns = trend + noise
        
        close_prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'date': dates,
            'open': close_prices * (1 + np.random.uniform(-0.003, 0.003, len(dates))),
            'high': close_prices * (1 + np.random.uniform(0.005, 0.015, len(dates))),
            'low': close_prices * (1 - np.random.uniform(0.005, 0.015, len(dates))),
            'close': close_prices,
            'volume': np.random.randint(5000000, 20000000, len(dates)),
            'adj close': close_prices
        })
        
        df['high'] = df[['high', 'open', 'close']].max(axis=1)
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        for col in ['open', 'high', 'low', 'close', 'adj close']:
            df[col] = df[col].round(2)
        
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df.columns = df.columns.str.lower()
        
        filepath = f'data/{filename}'
        df.to_csv(filepath, index=False)
        print(f"    ✓ Saved {filepath}")
    
    print()
    print("=" * 70)
    print(f"✅ SUCCESSFULLY CREATED SAMPLE DATA FOR {len(tickers) + len(indices)} STOCKS/INDICES!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run: python main.py")
    print("2. Open browser: http://localhost:8000/docs")
    print("3. Test endpoints: /detect and /signals")
    print()

if __name__ == "__main__":
    create_sample_data()
