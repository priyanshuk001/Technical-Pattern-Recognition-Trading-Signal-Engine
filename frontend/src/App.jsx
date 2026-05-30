import React from 'react';
import PatternDashboard from './components/PatternDashboard';

function App() {
  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-white">
            🕯️ Candlestick Pattern Detection System
          </h1>
          <p className="text-slate-400 mt-2">
            Indian Stock Market - Real-time Buy/Sell Recommendations
          </p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <PatternDashboard />
      </main>
      
      <footer className="bg-slate-800 border-t border-slate-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-slate-400">
          <p>Powered by FastAPI + React | Data from Yahoo Finance</p>
          <p className="text-sm mt-2">
            Disclaimer: This is for educational purposes. Not financial advice.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
