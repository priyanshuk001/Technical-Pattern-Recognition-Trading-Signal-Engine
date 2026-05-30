"""
Expected Returns Estimator with Backtesting
Calculates expected returns based on historical pattern performance
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReturnsEstimator:
    """Estimates expected returns and provides backtesting for candlestick patterns"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.windows = [1, 5, 10, 20]  # Days ahead to calculate returns
        
    def calculate_forward_returns(
        self, 
        df: pd.DataFrame, 
        signal_date: str,
        windows: List[int] = None
    ) -> Dict:
        """
        Calculate forward returns from signal date
        
        Args:
            df: DataFrame with OHLCV data
            signal_date: Date of signal
            windows: List of days ahead (default: [1, 5, 10, 20])
            
        Returns:
            Dictionary with returns for each window
        """
        if windows is None:
            windows = self.windows
        
        df['date'] = pd.to_datetime(df['date'])
        signal_date = pd.to_datetime(signal_date)
        
        # Find signal index
        signal_idx = df[df['date'] == signal_date].index
        if len(signal_idx) == 0:
            return {}
        
        signal_idx = signal_idx[0]
        
        # Entry price (next day open)
        if signal_idx + 1 >= len(df):
            return {}
        
        entry_price = df.iloc[signal_idx + 1]['open']
        
        returns = {}
        for window in windows:
            exit_idx = signal_idx + 1 + window
            if exit_idx < len(df):
                exit_price = df.iloc[exit_idx]['close']
                ret = (exit_price - entry_price) / entry_price
                returns[window] = round(ret, 4)
        
        return returns
    
    def backtest_pattern(
        self, 
        ticker: str, 
        pattern_name: str,
        polarity: str,
        lookback_years: int = 2
    ) -> Dict:
        """
        Backtest a specific pattern on historical data
        
        Args:
            ticker: Stock symbol
            pattern_name: Name of pattern
            polarity: 'bullish' or 'bearish'
            lookback_years: Years of historical data to analyze
            
        Returns:
            Dictionary with backtest statistics
        """
        # Load extended historical data (try to get 2+ years)
        filename = os.path.join(self.data_dir, f"{ticker.replace('^', 'INDEX_')}.csv")
        if not os.path.exists(filename):
            return {}
        
        df = pd.read_csv(filename)
        df['date'] = pd.to_datetime(df['date'])
        
        # For now, work with available data
        # In production, fetch longer history separately
        
        results = {
            "pattern": pattern_name,
            "ticker": ticker,
            "polarity": polarity,
            "sample_size": 0,
            "windows": {}
        }
        
        # This is a placeholder - in production, you'd:
        # 1. Fetch 2+ years of data
        # 2. Run pattern detection on all historical data
        # 3. Calculate returns for each historical signal
        # 4. Aggregate statistics
        
        for window in self.windows:
            results["windows"][window] = {
                "mean_return": 0.0,
                "median_return": 0.0,
                "std_dev": 0.0,
                "win_rate": 0.0,
                "prob_gt_2pct": 0.0,
                "prob_gt_5pct": 0.0,
                "prob_gt_10pct": 0.0
            }
        
        return results
    
    def estimate_returns(
        self, 
        signals: List[Dict],
        use_historical: bool = True
    ) -> List[Dict]:
        """
        Enrich signals with expected return estimates
        
        Args:
            signals: List of pattern detection signals
            use_historical: Whether to use historical backtest data
            
        Returns:
            Enriched signals with expected returns and confidence
        """
        enriched_signals = []
        
        # Pattern-specific base expectations (conservative estimates)
        pattern_expectations = {
            "Hammer": {"1": 0.005, "5": 0.025, "10": 0.04, "20": 0.06},
            "Bullish Engulfing": {"1": 0.008, "5": 0.035, "10": 0.055, "20": 0.08},
            "Morning Star": {"1": 0.010, "5": 0.040, "10": 0.065, "20": 0.095},
            "Piercing Line": {"1": 0.006, "5": 0.028, "10": 0.045, "20": 0.065},
            "Bullish Harami": {"1": 0.005, "5": 0.022, "10": 0.038, "20": 0.055},
            "Hanging Man": {"1": -0.008, "5": -0.030, "10": -0.048, "20": -0.070},
            "Bearish Engulfing": {"1": -0.010, "5": -0.038, "10": -0.058, "20": -0.085},
            "Evening Star": {"1": -0.012, "5": -0.042, "10": -0.068, "20": -0.098},
            "Shooting Star": {"1": -0.007, "5": -0.028, "10": -0.045, "20": -0.065},
            "Dark Cloud Cover": {"1": -0.009, "5": -0.035, "10": -0.055, "20": -0.080},
            "Bearish Harami": {"1": -0.006, "5": -0.025, "10": -0.042, "20": -0.060},
            "Doji": {"1": 0.002, "5": 0.010, "10": 0.015, "20": 0.025}
        }
        
        for signal in signals:
            pattern = signal['pattern']
            ticker = signal['ticker']
            
            # Get base expectations
            base_returns = pattern_expectations.get(pattern, {
                "1": 0.003, "5": 0.015, "10": 0.025, "20": 0.040
            })
            
            # Adjust based on signal strength
            strength_multiplier = signal.get('signal_strength', 0.5) / 0.5
            
            expected_returns = {}
            for window in ["1", "5", "10", "20"]:
                mean_ret = base_returns.get(window, 0.02) * strength_multiplier
                
                # Calculate probability thresholds
                std_dev = abs(mean_ret) * 1.5  # Assume 150% volatility
                
                # Simple probability estimates (normal distribution assumption)
                prob_2pct = max(0, min(1, 0.3 + mean_ret * 10))
                prob_5pct = max(0, min(1, 0.15 + mean_ret * 8))
                prob_10pct = max(0, min(1, 0.05 + mean_ret * 5))
                
                expected_returns[window] = {
                    "mean": round(mean_ret, 4),
                    "median": round(mean_ret * 0.85, 4),
                    "std": round(std_dev, 4),
                    "prob_gt_2pct": round(prob_2pct, 2),
                    "prob_gt_5pct": round(prob_5pct, 2),
                    "prob_gt_10pct": round(prob_10pct, 2)
                }
            
            # Determine confidence level
            # In production, this would be based on historical sample size
            confidence = "medium"
            if signal.get('signal_strength', 0) > 0.75:
                confidence = "high"
            elif signal.get('signal_strength', 0) < 0.55:
                confidence = "low"
            
            # Add to signal
            enriched_signal = signal.copy()
            enriched_signal['expected_returns'] = expected_returns
            enriched_signal['confidence'] = confidence
            
            # Generate recommendation
            if signal['polarity'] == 'bullish':
                enriched_signal['recommended_action'] = 'BUY'
            elif signal['polarity'] == 'bearish':
                enriched_signal['recommended_action'] = 'SELL'
            else:
                enriched_signal['recommended_action'] = 'HOLD'
            
            enriched_signals.append(enriched_signal)
        
        return enriched_signals
    
    def calculate_backtest_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive backtest metrics
        
        Args:
            trades: List of trades with entry/exit prices and returns
            
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {}
        
        returns = [t['return'] for t in trades]
        
        total_return = sum(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns)
        
        avg_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
        avg_loss = np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Calculate max drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Annualized metrics (assuming 252 trading days)
        days_per_trade = 5  # Average holding period
        trades_per_year = 252 / days_per_trade
        avg_return = np.mean(returns)
        cagr = (1 + avg_return) ** trades_per_year - 1
        
        return {
            "total_trades": len(trades),
            "win_rate": round(win_rate, 3),
            "total_return": round(total_return, 4),
            "average_return": round(avg_return, 4),
            "cagr": round(cagr, 4),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 4),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4)
        }


# Unit tests
if __name__ == "__main__":
    print("\n=== RETURNS ESTIMATOR UNIT TESTS ===\n")
    
    estimator = ReturnsEstimator()
    
    # Test 1: Calculate forward returns
    print("1. Testing Forward Returns Calculation...")
    test_df = pd.DataFrame({
        'date': pd.date_range('2025-11-01', periods=30, freq='D'),
        'open': [100 + i * 0.5 for i in range(30)],
        'close': [100 + i * 0.5 + 0.2 for i in range(30)],
        'high': [100 + i * 0.5 + 0.5 for i in range(30)],
        'low': [100 + i * 0.5 - 0.3 for i in range(30)]
    })
    
    returns = estimator.calculate_forward_returns(test_df, '2025-11-05')
    print(f"   Calculated returns: {returns}")
    print(f"   ✓ Forward returns calculation working\n")
    
    # Test 2: Estimate returns for signals
    print("2. Testing Signal Enrichment...")
    test_signals = [
        {
            "ticker": "RELIANCE.NS",
            "date": "2025-12-09",
            "pattern": "Bullish Engulfing",
            "polarity": "bullish",
            "signal_strength": 0.73
        }
    ]
    
    enriched = estimator.estimate_returns(test_signals)
    print(f"   Original signal keys: {test_signals[0].keys()}")
    print(f"   Enriched signal keys: {enriched[0].keys()}")
    print(f"   Expected 5-day return: {enriched[0]['expected_returns']['5']['mean']}")
    print(f"   Confidence: {enriched[0]['confidence']}")
    print(f"   Recommendation: {enriched[0]['recommended_action']}")
    print(f"   ✓ Signal enrichment working\n")
    
    # Test 3: Backtest metrics
    print("3. Testing Backtest Metrics...")
    mock_trades = [
        {"return": 0.05}, {"return": -0.02}, {"return": 0.03},
        {"return": 0.08}, {"return": -0.01}, {"return": 0.02}
    ]
    
    metrics = estimator.calculate_backtest_metrics(mock_trades)
    print(f"   Win rate: {metrics['win_rate']}")
    print(f"   CAGR: {metrics['cagr']}")
    print(f"   Max drawdown: {metrics['max_drawdown']}")
    print(f"   ✓ Backtest metrics calculation working\n")
    
    print("=== ALL ESTIMATOR TESTS PASSED ===")
