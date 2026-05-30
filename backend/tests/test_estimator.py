"""
Unit tests for returns estimator
"""

import pytest
import pandas as pd
import numpy as np
from estimator import ReturnsEstimator


@pytest.fixture
def estimator():
    return ReturnsEstimator(data_dir="test_data")


@pytest.fixture
def sample_data():
    """Create sample price data"""
    dates = pd.date_range('2025-10-01', periods=30, freq='D')
    return pd.DataFrame({
        'date': dates,
        'open': [100 + i * 0.5 for i in range(30)],
        'close': [100 + i * 0.5 + 0.2 for i in range(30)],
        'high': [100 + i * 0.5 + 0.5 for i in range(30)],
        'low': [100 + i * 0.5 - 0.3 for i in range(30)]
    })


def test_calculate_forward_returns(estimator, sample_data):
    """Test forward returns calculation"""
    returns = estimator.calculate_forward_returns(sample_data, '2025-10-05')
    
    assert isinstance(returns, dict)
    assert 1 in returns or 5 in returns
    
    # Returns should be positive for uptrending data
    if 1 in returns:
        assert returns[1] > 0


def test_estimate_returns_bullish(estimator):
    """Test return estimation for bullish pattern"""
    signals = [{
        "ticker": "TEST.NS",
        "date": "2025-12-09",
        "pattern": "Bullish Engulfing",
        "polarity": "bullish",
        "signal_strength": 0.75
    }]
    
    enriched = estimator.estimate_returns(signals)
    
    assert len(enriched) == 1
    assert 'expected_returns' in enriched[0]
    assert 'recommended_action' in enriched[0]
    assert enriched[0]['recommended_action'] == 'BUY'
    
    # Check 5-day return exists
    assert '5' in enriched[0]['expected_returns']
    assert enriched[0]['expected_returns']['5']['mean'] > 0


def test_estimate_returns_bearish(estimator):
    """Test return estimation for bearish pattern"""
    signals = [{
        "ticker": "TEST.NS",
        "date": "2025-12-09",
        "pattern": "Bearish Engulfing",
        "polarity": "bearish",
        "signal_strength": 0.70
    }]
    
    enriched = estimator.estimate_returns(signals)
    
    assert enriched[0]['recommended_action'] == 'SELL'
    assert enriched[0]['expected_returns']['5']['mean'] < 0


def test_backtest_metrics(estimator):
    """Test backtest metrics calculation"""
    trades = [
        {"return": 0.05},
        {"return": -0.02},
        {"return": 0.03},
        {"return": 0.08},
        {"return": -0.01}
    ]
    
    metrics = estimator.calculate_backtest_metrics(trades)
    
    assert 'win_rate' in metrics
    assert 'cagr' in metrics
    assert 'max_drawdown' in metrics
    assert 0 <= metrics['win_rate'] <= 1
    assert metrics['total_trades'] == 5


def test_confidence_assignment(estimator):
    """Test confidence level assignment"""
    # High strength signal
    high_signal = [{
        "ticker": "TEST.NS",
        "date": "2025-12-09",
        "pattern": "Morning Star",
        "polarity": "bullish",
        "signal_strength": 0.85
    }]
    
    enriched = estimator.estimate_returns(high_signal)
    assert enriched[0]['confidence'] == 'high'
    
    # Low strength signal
    low_signal = [{
        "ticker": "TEST.NS",
        "date": "2025-12-09",
        "pattern": "Doji",
        "polarity": "neutral",
        "signal_strength": 0.50
    }]
    
    enriched = estimator.estimate_returns(low_signal)
    assert enriched[0]['confidence'] == 'low'
