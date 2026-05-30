"""
FastAPI Backend for Candlestick Pattern Detection System
Serves pattern detection results and recommendations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import os
import json
from datetime import datetime

from data_fetcher import DataFetcher
from pattern_detector import PatternDetector
from estimator import ReturnsEstimator

# Initialize FastAPI app
app = FastAPI(
    title="Candlestick Pattern Detection API",
    description="Detects candlestick patterns in Indian stock market and provides recommendations",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
data_fetcher = DataFetcher(data_dir="data")
pattern_detector = PatternDetector(data_dir="data")
returns_estimator = ReturnsEstimator(data_dir="data")

# Cache for signals
signals_cache = {
    "signals": [],
    "last_updated": None
}


# Response Models
class Signal(BaseModel):
    ticker: str
    date: str
    pattern: str
    polarity: str
    signal_strength: float
    recommended_action: str
    expected_returns: Dict
    confidence: str
    pattern_bars: List[str]


class SignalsResponse(BaseModel):
    signals: List[Dict]
    last_updated: Optional[str]
    total_count: int


class UpdateResponse(BaseModel):
    status: str
    success_count: int
    failed_count: int
    failed_tickers: List[str]


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Candlestick Pattern Detection API",
        "version": "1.0.0",
        "endpoints": [
            "/update_data",
            "/detect",
            "/signals",
            "/chart/{ticker}"
        ]
    }


@app.get("/update_data", response_model=UpdateResponse)
def update_data(months: int = 2):
    """
    Fetch latest OHLCV data for all tickers
    
    Args:
        months: Number of months of historical data (default: 2)
    """
    try:
        results = data_fetcher.fetch_all(months=months)
        
        return UpdateResponse(
            status="completed",
            success_count=results["success"],
            failed_count=results["failed"],
            failed_tickers=results["failed_tickers"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/detect")
def detect_patterns():
    """
    Run pattern detection on all available data
    Returns detected patterns without return estimates
    """
    try:
        # Detect patterns
        signals = pattern_detector.detect_all(data_dir="data")
        
        # Update cache
        signals_cache["signals"] = signals
        signals_cache["last_updated"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "patterns_detected": len(signals),
            "last_updated": signals_cache["last_updated"],
            "signals": signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals", response_model=SignalsResponse)
def get_signals(
    pattern: Optional[str] = None,
    polarity: Optional[str] = None,
    min_strength: Optional[float] = None
):
    """
    Get all signals with expected returns and recommendations
    
    Query parameters:
        pattern: Filter by pattern name
        polarity: Filter by 'bullish' or 'bearish'
        min_strength: Minimum signal strength (0-1)
    """
    try:
        # If cache is empty, run detection
        if not signals_cache["signals"]:
            signals = pattern_detector.detect_all(data_dir="data")
            signals_cache["signals"] = signals
            signals_cache["last_updated"] = datetime.now().isoformat()
        
        # Enrich with expected returns
        enriched_signals = returns_estimator.estimate_returns(signals_cache["signals"])
        
        # Apply filters
        filtered_signals = enriched_signals
        
        if pattern:
            filtered_signals = [s for s in filtered_signals if s["pattern"] == pattern]
        
        if polarity:
            filtered_signals = [s for s in filtered_signals if s["polarity"] == polarity]
        
        if min_strength:
            filtered_signals = [s for s in filtered_signals if s["signal_strength"] >= min_strength]
        
        # Sort by date (most recent first) and signal strength
        filtered_signals.sort(
            key=lambda x: (x["date"], x["signal_strength"]),
            reverse=True
        )
        
        return SignalsResponse(
            signals=filtered_signals,
            last_updated=signals_cache["last_updated"],
            total_count=len(filtered_signals)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chart/{ticker}")
def get_chart_data(ticker: str):
    """
    Get OHLCV data for a specific ticker for charting
    
    Args:
        ticker: Stock symbol (e.g., 'RELIANCE.NS')
    """
    try:
        df = data_fetcher.load_data(ticker)
        
        if df is None:
            raise HTTPException(status_code=404, detail=f"Data not found for {ticker}")
        
        # Convert to list of dicts for JSON response
        df['date'] = df['date'].astype(str)
        chart_data = df.to_dict('records')
        
        return {
            "ticker": ticker,
            "data": chart_data,
            "total_bars": len(chart_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/{ticker}/{pattern}")
def backtest_pattern(ticker: str, pattern: str):
    """
    Get backtest results for a specific pattern on a ticker
    
    Args:
        ticker: Stock symbol
        pattern: Pattern name
    """
    try:
        # This is a placeholder - full implementation would require
        # extended historical data and comprehensive backtesting
        
        return {
            "ticker": ticker,
            "pattern": pattern,
            "message": "Backtest endpoint - implement with extended historical data",
            "recommendation": "Use /signals endpoint for pattern-based recommendations"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patterns")
def list_patterns():
    """Get list of all supported patterns"""
    patterns = [
        {"name": "Hammer", "polarity": "bullish", "candles": 1},
        {"name": "Hanging Man", "polarity": "bearish", "candles": 1},
        {"name": "Bullish Engulfing", "polarity": "bullish", "candles": 2},
        {"name": "Bearish Engulfing", "polarity": "bearish", "candles": 2},
        {"name": "Doji", "polarity": "neutral", "candles": 1},
        {"name": "Morning Star", "polarity": "bullish", "candles": 3},
        {"name": "Evening Star", "polarity": "bearish", "candles": 3},
        {"name": "Shooting Star", "polarity": "bearish", "candles": 1},
        {"name": "Piercing Line", "polarity": "bullish", "candles": 2},
        {"name": "Dark Cloud Cover", "polarity": "bearish", "candles": 2},
        {"name": "Bullish Harami", "polarity": "bullish", "candles": 2},
        {"name": "Bearish Harami", "polarity": "bearish", "candles": 2}
    ]
    
    return {"patterns": patterns, "total": len(patterns)}


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Run server - use import string for reload to work
    uvicorn.run(
        "main:app",  # ← Import string instead of app instance
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
