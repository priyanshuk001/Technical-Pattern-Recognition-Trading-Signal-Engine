import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Eye, ArrowUpDown } from 'lucide-react';

const SignalTable = ({ signals, onViewDetails }) => {
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'desc' ? 'asc' : 'desc'
    });
  };

  const sortedSignals = [...signals].sort((a, b) => {
    let aVal = a[sortConfig.key];
    let bVal = b[sortConfig.key];

    // Special handling for nested values
    if (sortConfig.key === 'expected_return_5d') {
      aVal = a.expected_returns?.['5']?.mean || 0;
      bVal = b.expected_returns?.['5']?.mean || 0;
    }

    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const getPolarityColor = (polarity) => {
    if (polarity === 'bullish') return 'text-green-500';
    if (polarity === 'bearish') return 'text-red-500';
    return 'text-slate-400';
  };

  const getConfidenceBadge = (confidence) => {
    const colors = {
      high: 'bg-green-900/30 text-green-500 border-green-500',
      medium: 'bg-yellow-900/30 text-yellow-500 border-yellow-500',
      low: 'bg-slate-700 text-slate-400 border-slate-600'
    };
    return colors[confidence] || colors.low;
  };

  if (signals.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-12 border border-slate-700 text-center">
        <p className="text-slate-400">No signals found. Try updating data or adjusting filters.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-900/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                <button onClick={() => handleSort('ticker')} className="flex items-center gap-1 hover:text-white">
                  Ticker <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                <button onClick={() => handleSort('date')} className="flex items-center gap-1 hover:text-white">
                  Date <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Pattern
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Signal
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                <button onClick={() => handleSort('signal_strength')} className="flex items-center gap-1 hover:text-white">
                  Strength <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                5D Return
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {sortedSignals.map((signal, idx) => (
              <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-white">
                  {signal.ticker.replace('.NS', '')}
                </td>
                <td className="px-4 py-3 text-sm text-slate-300">
                  {new Date(signal.date).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-sm text-slate-300">
                  {signal.pattern}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className={`flex items-center gap-1 font-medium ${getPolarityColor(signal.polarity)}`}>
                    {signal.polarity === 'bullish' && <TrendingUp className="w-4 h-4" />}
                    {signal.polarity === 'bearish' && <TrendingDown className="w-4 h-4" />}
                    {signal.recommended_action}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${signal.signal_strength * 100}%` }}
                      />
                    </div>
                    <span className="text-slate-400">{(signal.signal_strength * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`font-medium ${
                    signal.expected_returns?.['5']?.mean > 0 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {signal.expected_returns?.['5']?.mean 
                      ? `${(signal.expected_returns['5'].mean * 100).toFixed(2)}%`
                      : 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getConfidenceBadge(signal.confidence)}`}>
                    {signal.confidence}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <button
                    onClick={() => onViewDetails(signal)}
                    className="flex items-center gap-1 text-blue-500 hover:text-blue-400 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SignalTable;
