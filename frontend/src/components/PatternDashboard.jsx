import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import SignalTable from './SignalTable';
import PatternChart from './PatternChart';
import { patternAPI } from '../api';

const PatternDashboard = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [filters, setFilters] = useState({
    polarity: '',
    pattern: '',
    min_strength: 0
  });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);

  // Fetch signals on mount
  useEffect(() => {
    fetchSignals();
  }, [filters]);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patternAPI.getSignals(filters);
      setSignals(data.signals);
      setLastUpdated(data.last_updated);
    } catch (err) {
      setError('Failed to fetch signals. Please ensure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateData = async () => {
    try {
      setIsUpdating(true);
      await patternAPI.updateData(2);
      await patternAPI.detectPatterns();
      await fetchSignals();
      alert('Data updated successfully!');
    } catch (err) {
      alert('Failed to update data: ' + err.message);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleViewDetails = (signal) => {
    setSelectedSignal(signal);
  };

  const handleCloseDetails = () => {
    setSelectedSignal(null);
  };

  // Calculate stats
  const stats = {
    total: signals.length,
    bullish: signals.filter(s => s.polarity === 'bullish').length,
    bearish: signals.filter(s => s.polarity === 'bearish').length,
    highConfidence: signals.filter(s => s.confidence === 'high').length
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-slate-400 text-sm font-medium">Total Signals</h3>
          <p className="text-3xl font-bold text-white mt-2">{stats.total}</p>
        </div>
        
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-slate-400 text-sm font-medium flex items-center">
            <TrendingUp className="w-4 h-4 mr-2 text-green-500" />
            Bullish
          </h3>
          <p className="text-3xl font-bold text-green-500 mt-2">{stats.bullish}</p>
        </div>
        
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-slate-400 text-sm font-medium flex items-center">
            <TrendingDown className="w-4 h-4 mr-2 text-red-500" />
            Bearish
          </h3>
          <p className="text-3xl font-bold text-red-500 mt-2">{stats.bearish}</p>
        </div>
        
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-slate-400 text-sm font-medium">High Confidence</h3>
          <p className="text-3xl font-bold text-blue-500 mt-2">{stats.highConfidence}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={handleUpdateData}
              disabled={isUpdating}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isUpdating ? 'animate-spin' : ''}`} />
              {isUpdating ? 'Updating...' : 'Update Data'}
            </button>

            <button
              onClick={fetchSignals}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {lastUpdated && (
            <div className="text-sm text-slate-400">
              Last updated: {new Date(lastUpdated).toLocaleString()}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-4">
          <select
            value={filters.polarity}
            onChange={(e) => setFilters({ ...filters, polarity: e.target.value })}
            className="bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-600"
          >
            <option value="">All Polarities</option>
            <option value="bullish">Bullish Only</option>
            <option value="bearish">Bearish Only</option>
          </select>

          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={filters.min_strength}
            onChange={(e) => setFilters({ ...filters, min_strength: parseFloat(e.target.value) })}
            placeholder="Min Strength (0-1)"
            className="bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-600"
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-red-500 font-medium">Error</h4>
            <p className="text-red-300 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Signals Table */}
      {loading ? (
        <div className="bg-slate-800 rounded-lg p-12 border border-slate-700 text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
          <p className="text-slate-400 mt-4">Loading signals...</p>
        </div>
      ) : (
        <SignalTable 
          signals={signals} 
          onViewDetails={handleViewDetails}
        />
      )}

      {/* Pattern Chart Modal */}
      {selectedSignal && (
        <PatternChart 
          signal={selectedSignal}
          onClose={handleCloseDetails}
        />
      )}
    </div>
  );
};

export default PatternDashboard;
