/**
 * API Configuration
 *
 * Centralized API URL configuration with environment variable support.
 * Uses REACT_APP_API_URL environment variable or falls back to localhost.
 */

// Get API URL from environment or use default
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// API endpoints configuration
export const API_ENDPOINTS = {
  // Stock data
  stocks: `${API_BASE_URL}/api/stocks`,
  stockData: `${API_BASE_URL}/api/stock-data`,

  // Anomalies
  anomalies: `${API_BASE_URL}/api/anomalies`,

  // Settings
  settings: `${API_BASE_URL}/api/settings`,

  // Health
  health: `${API_BASE_URL}/api/health`,
  ready: `${API_BASE_URL}/api/ready`,

  // Detection
  detectAnomalies: `${API_BASE_URL}/api/detect-anomalies`,
  detectionStatus: `${API_BASE_URL}/api/detection/status`,
  models: `${API_BASE_URL}/api/models`,

  // Alerts
  alertStatus: `${API_BASE_URL}/api/alerts/status`,
  alertHistory: `${API_BASE_URL}/api/alerts/history`,
};

/**
 * Build URL with query parameters
 */
export const buildUrl = (endpoint, params = {}) => {
  const url = new URL(endpoint);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.append(key, value);
    }
  });
  return url.toString();
};

/**
 * API fetch wrapper with error handling
 */
export const apiFetch = async (url, options = {}) => {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, mergedOptions);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP error ${response.status}`,
        response.status,
        errorData.error_code,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "Network error", 0, "NETWORK_ERROR");
  }
};

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export default API_BASE_URL;
