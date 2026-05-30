import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const patternAPI = {
  // Update data
  updateData: async (months = 2) => {
    const response = await api.get(`/update_data?months=${months}`);
    return response.data;
  },

  // Detect patterns
  detectPatterns: async () => {
    const response = await api.get('/detect');
    return response.data;
  },

  // Get all signals with filters
  getSignals: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.pattern) params.append('pattern', filters.pattern);
    if (filters.polarity) params.append('polarity', filters.polarity);
    if (filters.min_strength) params.append('min_strength', filters.min_strength);
    
    const response = await api.get(`/signals?${params.toString()}`);
    return response.data;
  },

  // Get chart data for ticker
  getChartData: async (ticker) => {
    const response = await api.get(`/chart/${ticker}`);
    return response.data;
  },

  // Get list of patterns
  getPatterns: async () => {
    const response = await api.get('/patterns');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};

export default api;
