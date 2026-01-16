/**
 * Date Validation Tests
 */

import { 
  validateDateRange, 
  formatDate, 
  parseDate,
  getDatePresets 
} from '../dateValidation';

describe('validateDateRange', () => {
  test('returns valid for correct date range', () => {
    const start = new Date('2024-01-01');
    const end = new Date('2024-01-31');
    const result = validateDateRange(start, end);
    
    expect(result.isValid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('returns error when start date is after end date', () => {
    const start = new Date('2024-02-01');
    const end = new Date('2024-01-01');
    const result = validateDateRange(start, end);
    
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('before or equal');
  });

  test('returns error when start date is null', () => {
    const end = new Date('2024-01-31');
    const result = validateDateRange(null, end);
    
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('required');
  });

  test('returns error when end date is null', () => {
    const start = new Date('2024-01-01');
    const result = validateDateRange(start, null);
    
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('required');
  });

  test('returns valid when start equals end', () => {
    const date = new Date('2024-01-15');
    const result = validateDateRange(date, date);
    
    expect(result.isValid).toBe(true);
  });

  test('returns error for date range exceeding 5 years', () => {
    const start = new Date('2019-01-01');
    const end = new Date('2025-01-01');
    const result = validateDateRange(start, end);
    
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('exceed');
  });

  test('returns error for invalid date string', () => {
    const start = new Date('invalid');
    const end = new Date('2024-01-31');
    const result = validateDateRange(start, end);
    
    expect(result.isValid).toBe(false);
  });
});

describe('formatDate', () => {
  test('formats date in short format', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date, 'short');
    
    expect(result).toContain('2024');
    expect(result).toContain('Jan');
  });

  test('formats date in ISO format', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date, 'iso');
    
    expect(result).toBe('2024-01-15');
  });

  test('formats date in long format', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date, 'long');
    
    expect(result).toContain('January');
    expect(result).toContain('2024');
  });

  test('handles invalid date', () => {
    const result = formatDate('invalid');
    expect(result).toBe('Invalid date');
  });

  test('handles date string input', () => {
    const result = formatDate('2024-01-15', 'iso');
    expect(result).toBe('2024-01-15');
  });
});

describe('parseDate', () => {
  test('parses valid date string', () => {
    const result = parseDate('2024-01-15');
    
    expect(result).toBeInstanceOf(Date);
    expect(result.getFullYear()).toBe(2024);
  });

  test('returns null for invalid date', () => {
    const result = parseDate('invalid');
    expect(result).toBeNull();
  });

  test('returns null for empty input', () => {
    expect(parseDate(null)).toBeNull();
    expect(parseDate(undefined)).toBeNull();
    expect(parseDate('')).toBeNull();
  });

  test('returns Date object for Date input', () => {
    const input = new Date('2024-01-15');
    const result = parseDate(input);
    
    expect(result).toBeInstanceOf(Date);
    expect(result.getTime()).toBe(input.getTime());
  });
});

describe('getDatePresets', () => {
  test('returns array of presets', () => {
    const presets = getDatePresets();
    
    expect(Array.isArray(presets)).toBe(true);
    expect(presets.length).toBeGreaterThan(0);
  });

  test('each preset has required properties', () => {
    const presets = getDatePresets();
    
    presets.forEach(preset => {
      expect(preset).toHaveProperty('label');
      expect(preset).toHaveProperty('value');
      expect(preset).toHaveProperty('getRange');
      expect(typeof preset.getRange).toBe('function');
    });
  });

  test('preset getRange returns valid date range', () => {
    const presets = getDatePresets();
    const preset = presets[0]; // Last 7 days
    
    const range = preset.getRange();
    expect(range).toHaveProperty('start');
    expect(range).toHaveProperty('end');
    expect(range.start).toBeInstanceOf(Date);
    expect(range.end).toBeInstanceOf(Date);
    expect(range.start < range.end).toBe(true);
  });
});
