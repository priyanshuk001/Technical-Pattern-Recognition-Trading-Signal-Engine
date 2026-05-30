import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { X, TrendingUp, TrendingDown } from 'lucide-react';
import { patternAPI } from '../api';

const PatternChart = ({ signal, onClose }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChartData();
  }, [signal.ticker]);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      const data = await patternAPI.getChartData(signal.ticker);
      setChartData(data);
      renderChart(data.data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderChart = (data) => {
    if (!chartContainerRef.current) return;

    // Clear existing chart
    if (chartRef.current) {
      chartRef.current.remove();
    }

    // Create new chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1e293b' },
        textColor: '#e2e8f0',
      },
      grid: {
        vertLines: { color: '#334155' },
        horzLines: { color: '#334155' },
      },
      timeScale: {
        borderColor: '#475569',
      },
    });

    chartRef.current = chart;

    // Prepare candlestick data
    const candleData = data.map(item => ({
      time: item.date,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candleSeries.setData(candleData);

    // Add markers for pattern bars
    const markers = signal.pattern_bars.map(date => ({
      time: date,
      position: signal.polarity === 'bullish' ? 'belowBar' : 'aboveBar',
      color: signal.polarity === 'bullish' ? '#10b981' : '#ef4444',
      shape: 'arrowUp',
      text: signal.pattern,
    }));

    candleSeries.setMarkers(markers);

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  };

  // Calculate stop loss and target
  const currentPrice = chartData?.data[chartData.data.length - 1]?.close || 0;
  const stopLoss = currentPrice * (signal.polarity === 'bullish' ? 0.98 : 1.02);
  const expectedReturn = signal.expected_returns?.['5']?.mean || 0;
  const target = currentPrice * (1 + expectedReturn);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-lg border border-slate-700 max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              {signal.ticker.replace('.NS', '')}
              {signal.polarity === 'bullish' ? (
                <TrendingUp className="text-green-500" />
              ) : (
                <TrendingDown className="text-red-500" />
              )}
            </h2>
            <p className="text-slate-400 mt-1">
              {signal.pattern} - {new Date(signal.date).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Chart */}
        <div className="p-6">
          {loading ? (
            <div className="h-96 flex items-center justify-center">
              <p className="text-slate-400">Loading chart...</p>
            </div>
          ) : (
            <div ref={chartContainerRef} className="w-full" />
          )}
        </div>

        {/* Details */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-slate-700">
          {/* Left Column */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Pattern Details</h3>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Signal Strength:</span>
                <span className="text-white font-medium">
                  {(signal.signal_strength * 100).toFixed(0)}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-slate-400">Confidence:</span>
                <span className="text-white font-medium capitalize">{signal.confidence}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-slate-400">Recommendation:</span>
                <span className={`font-bold ${
                  signal.recommended_action === 'BUY' ? 'text-green-500' : 'text-red-500'
                }`}>
                  {signal.recommended_action}
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-700">
              <h4 className="text-sm font-semibold text-slate-400 mb-2">Trading Levels</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Current Price:</span>
                  <span className="text-white font-mono">₹{currentPrice.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Stop Loss:</span>
                  <span className="text-red-500 font-mono">₹{stopLoss.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Target (5D):</span>
                  <span className="text-green-500 font-mono">₹{target.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Expected Returns */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Expected Returns</h3>
            
            <div className="space-y-3">
              {['1', '5', '10', '20'].map(window => {
                const returns = signal.expected_returns?.[window];
                if (!returns) return null;
                
                return (
                  <div key={window} className="bg-slate-900/50 rounded p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-slate-300 font-medium">{window} Day{window !== '1' ? 's' : ''}</span>
                      <span className={`font-bold ${
                        returns.mean > 0 ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {(returns.mean * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <div className="text-slate-500">Median</div>
                        <div className="text-slate-300">{(returns.median * 100).toFixed(2)}%</div>
                      </div>
                      <div>
                        <div className="text-slate-500">Std Dev</div>
                        <div className="text-slate-300">{(returns.std * 100).toFixed(2)}%</div>
                      </div>
                      <div>
                        <div className="text-slate-500">P(&gt;2%)</div>
                        <div className="text-slate-300">{(returns.prob_gt_2pct * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatternChart;
