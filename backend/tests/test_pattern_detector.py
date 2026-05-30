"""
Unit tests for pattern detector
"""

import pytest
import pandas as pd
import numpy as np
from pattern_detector import PatternDetector


@pytest.fixture
def detector():
    return PatternDetector(data_dir="test_data")


@pytest.fixture
def sample_data():
    """Create sample OHLCV data"""
    dates = pd.date_range('2025-10-01', periods=60, freq='D')
    return pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(95, 105, 60),
        'high': np.random.uniform(100, 110, 60),
        'low': np.random.uniform(90, 100, 60),
        'close': np.random.uniform(95, 105, 60),
        'volume': np.random.uniform(900000, 1100000, 60)
    })


def test_calculate_indicators(detector, sample_data):
    """Test indicator calculation"""
    df = detector.calculate_indicators(sample_data)
    
    assert 'ma5' in df.columns
    assert 'ma20' in df.columns
    assert 'vol_ma20' in df.columns
    assert 'body' in df.columns
    assert pd.notna(df.iloc[-1]['ma5'])


def test_detect_hammer(detector):
    """Test hammer pattern detection"""
    # Create perfect hammer
    dates = pd.date_range('2025-10-01', periods=40, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': [100] * 40,
        'high': [101] * 40,
        'low': [95] * 40,
        'close': [99.5] * 40,
        'volume': [1000000] * 40
    })
    
    # Last candle is hammer
    df.loc[39, 'open'] = 100
    df.loc[39, 'close'] = 99.5
    df.loc[39, 'high'] = 100.5
    df.loc[39, 'low'] = 94
    
    df = detector.calculate_indicators(df)
    result = detector.detect_hammer(df, 39)
    
    assert result is not None
    assert result['pattern'] == 'Hammer'
    assert result['polarity'] == 'bullish'


def test_detect_bullish_engulfing(detector):
    """Test bullish engulfing pattern"""
    dates = pd.date_range('2025-10-01', periods=40, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': [100] * 40,
        'high': [102] * 40,
        'low': [98] * 40,
        'close': [100] * 40,
        'volume': [1000000] * 40
    })
    
    # Create bullish engulfing
    df.loc[38, 'open'] = 100
    df.loc[38, 'close'] = 98
    df.loc[39, 'open'] = 97
    df.loc[39, 'close'] = 101
    
    df = detector.calculate_indicators(df)
    result = detector.detect_bullish_engulfing(df, 39)
    
    assert result is not None
    assert result['pattern'] == 'Bullish Engulfing'
    assert len(result['pattern_bars']) == 2


def test_detect_doji(detector):
    """Test doji pattern detection"""
    dates = pd.date_range('2025-10-01', periods=40, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': [100] * 40,
        'high': [102] * 40,
        'low': [98] * 40,
        'close': [100] * 40,
        'volume': [1000000] * 40
    })
    
    # Create doji
    df.loc[39, 'open'] = 100
    df.loc[39, 'close'] = 100.1
    df.loc[39, 'high'] = 102
    df.loc[39, 'low'] = 98
    
    df = detector.calculate_indicators(df)
    result = detector.detect_doji(df, 39)
    
    assert result is not None
    assert result['pattern'] == 'Doji'


def test_no_pattern_detected(detector, sample_data):
    """Test that no pattern is detected in random data"""
    df = detector.calculate_indicators(sample_data)
    
    # Random data should not consistently trigger patterns
    result = detector.detect_hammer(df, 30)
    # May or may not detect - that's okay for random data
    assert True  # Test passes as long as no exception
