/**
 * API Configuration Tests
 */

import API_BASE_URL, { API_ENDPOINTS, buildUrl, apiFetch, ApiError } from './api';

describe('API Configuration', () => {
  test('exports API_BASE_URL', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(typeof API_BASE_URL).toBe('string');
  });

  test('exports all required endpoints', () => {
    expect(API_ENDPOINTS.stocks).toBeDefined();
    expect(API_ENDPOINTS.stockData).toBeDefined();
    expect(API_ENDPOINTS.anomalies).toBeDefined();
    expect(API_ENDPOINTS.settings).toBeDefined();
    expect(API_ENDPOINTS.health).toBeDefined();
    expect(API_ENDPOINTS.detectAnomalies).toBeDefined();
  });

  test('endpoints contain base URL', () => {
    expect(API_ENDPOINTS.stocks).toContain(API_BASE_URL);
    expect(API_ENDPOINTS.anomalies).toContain(API_BASE_URL);
  });
});

describe('buildUrl', () => {
  test('builds URL without params', () => {
    const url = buildUrl('http://localhost:8000/api/test');
    expect(url).toBe('http://localhost:8000/api/test');
  });

  test('builds URL with single param', () => {
    const url = buildUrl('http://localhost:8000/api/test', { symbol: 'AAPL' });
    expect(url).toContain('symbol=AAPL');
  });

  test('builds URL with multiple params', () => {
    const url = buildUrl('http://localhost:8000/api/test', { 
      symbol: 'AAPL',
      limit: 100 
    });
    expect(url).toContain('symbol=AAPL');
    expect(url).toContain('limit=100');
  });

  test('ignores null/undefined params', () => {
    const url = buildUrl('http://localhost:8000/api/test', { 
      symbol: 'AAPL',
      start: null,
      end: undefined 
    });
    expect(url).toContain('symbol=AAPL');
    expect(url).not.toContain('start');
    expect(url).not.toContain('end');
  });

  test('ignores empty string params', () => {
    const url = buildUrl('http://localhost:8000/api/test', { 
      symbol: 'AAPL',
      filter: '' 
    });
    expect(url).toContain('symbol=AAPL');
    expect(url).not.toContain('filter');
  });
});

describe('ApiError', () => {
  test('creates error with message, status, and code', () => {
    const error = new ApiError('Not found', 404, 'NOT_FOUND');
    
    expect(error.message).toBe('Not found');
    expect(error.status).toBe(404);
    expect(error.code).toBe('NOT_FOUND');
    expect(error.name).toBe('ApiError');
  });

  test('is instance of Error', () => {
    const error = new ApiError('Test error', 500);
    expect(error).toBeInstanceOf(Error);
  });
});

describe('apiFetch', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  test('returns data for successful response', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });

    const result = await apiFetch('http://localhost:8000/api/test');
    expect(result).toEqual({ data: 'test' });
  });

  test('throws ApiError for failed response', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: 'Not found', error_code: 'NOT_FOUND' }),
    });

    await expect(apiFetch('http://localhost:8000/api/test'))
      .rejects
      .toThrow(ApiError);
  });

  test('includes correct headers', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    await apiFetch('http://localhost:8000/api/test');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  test('handles network errors', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    await expect(apiFetch('http://localhost:8000/api/test'))
      .rejects
      .toThrow('Network error');
  });

  test('preserves custom options', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    await apiFetch('http://localhost:8000/api/test', {
      method: 'POST',
      body: JSON.stringify({ data: 'test' }),
    });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
      })
    );
  });
});
