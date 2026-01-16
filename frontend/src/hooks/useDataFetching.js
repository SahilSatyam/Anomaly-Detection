/**
 * Custom React Hooks
 * 
 * Provides hooks for data fetching, polling, and state management.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { API_ENDPOINTS, buildUrl, apiFetch } from '../config/api';

/**
 * Hook for fetching data with loading and error states
 * @param {Function} fetchFn - Async function that fetches data
 * @param {Array} deps - Dependency array for re-fetching
 */
export const useFetch = (fetchFn, deps = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    fetch();
  }, [...deps, fetch]);

  return { data, loading, error, refetch: fetch };
};

/**
 * Hook for stock data with auto-refresh/polling
 * @param {string} symbol - Stock symbol
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional options
 */
export const useStockData = (symbol, startDate, endDate, options = {}) => {
  const { 
    autoRefresh = false, 
    refreshInterval = 60000, // 1 minute default
    enabled = true 
  } = options;

  const [stockData, setStockData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async (silent = false) => {
    if (!symbol || !enabled) return;

    if (!silent) {
      setLoading(true);
    }
    setError(null);

    try {
      const stockUrl = buildUrl(API_ENDPOINTS.stockData, {
        symbol,
        start: startDate?.toISOString(),
        end: endDate?.toISOString(),
      });

      const anomaliesUrl = buildUrl(API_ENDPOINTS.anomalies, {
        symbol,
        start: startDate?.toISOString(),
        end: endDate?.toISOString(),
      });

      const [stockResponse, anomaliesResponse] = await Promise.all([
        apiFetch(stockUrl),
        apiFetch(anomaliesUrl),
      ]);

      if (mountedRef.current) {
        setStockData(stockResponse.data || []);
        setAnomalies(anomaliesResponse.data || []);
        setLastUpdated(new Date());
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message || 'Failed to fetch data');
      }
    } finally {
      if (mountedRef.current && !silent) {
        setLoading(false);
      }
    }
  }, [symbol, startDate, endDate, enabled]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh polling
  useEffect(() => {
    if (autoRefresh && enabled) {
      intervalRef.current = setInterval(() => {
        fetchData(true); // Silent refresh
      }, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, enabled, fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    stockData,
    anomalies,
    loading,
    error,
    lastUpdated,
    refetch: () => fetchData(false),
    silentRefresh: () => fetchData(true),
  };
};

/**
 * Hook for polling with WebSocket fallback concept
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Polling options
 */
export const usePolling = (endpoint, options = {}) => {
  const {
    interval = 30000,
    enabled = true,
    onData = () => {},
    onError = () => {},
  } = options;

  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  const poll = useCallback(async () => {
    try {
      const data = await apiFetch(endpoint);
      if (mountedRef.current) {
        onData(data);
      }
    } catch (err) {
      if (mountedRef.current) {
        onError(err);
      }
    }
  }, [endpoint, onData, onError]);

  const startPolling = useCallback(() => {
    if (!enabled || intervalRef.current) return;
    
    setIsPolling(true);
    poll(); // Initial fetch
    intervalRef.current = setInterval(poll, interval);
  }, [enabled, interval, poll]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [enabled, startPolling, stopPolling]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return { isPolling, startPolling, stopPolling, poll };
};

/**
 * Hook for detection status with periodic updates
 */
export const useDetectionStatus = (enabled = true) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiFetch(API_ENDPOINTS.detectionStatus);
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      fetchStatus();
    }
  }, [enabled, fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
};

/**
 * Hook for health check
 */
export const useHealthCheck = (pollInterval = 30000) => {
  const [health, setHealth] = useState(null);
  const [isHealthy, setIsHealthy] = useState(true);
  
  const { isPolling } = usePolling(API_ENDPOINTS.health, {
    interval: pollInterval,
    enabled: true,
    onData: (data) => {
      setHealth(data);
      setIsHealthy(data.status === 'healthy');
    },
    onError: () => {
      setIsHealthy(false);
    },
  });

  return { health, isHealthy, isPolling };
};

/**
 * Hook for managing local storage state
 */
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
};

/**
 * Hook for debounced value
 */
export const useDebounce = (value, delay = 500) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

export default {
  useFetch,
  useStockData,
  usePolling,
  useDetectionStatus,
  useHealthCheck,
  useLocalStorage,
  useDebounce,
};
