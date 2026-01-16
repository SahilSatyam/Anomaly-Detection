/**
 * Export Data Utilities Tests
 */

import { convertToCSV, exportStockDataCSV, exportAnomaliesCSV } from '../exportData';

describe('convertToCSV', () => {
  test('converts array of objects to CSV', () => {
    const data = [
      { name: 'John', age: 30 },
      { name: 'Jane', age: 25 },
    ];
    
    const result = convertToCSV(data);
    
    expect(result).toContain('name');
    expect(result).toContain('age');
    expect(result).toContain('John');
    expect(result).toContain('30');
  });

  test('returns empty string for empty array', () => {
    const result = convertToCSV([]);
    expect(result).toBe('');
  });

  test('returns empty string for null/undefined', () => {
    expect(convertToCSV(null)).toBe('');
    expect(convertToCSV(undefined)).toBe('');
  });

  test('handles custom columns', () => {
    const data = [
      { name: 'John', age: 30, city: 'NYC' },
    ];
    
    const result = convertToCSV(data, { columns: ['name', 'age'] });
    
    expect(result).toContain('name');
    expect(result).toContain('age');
    expect(result).not.toContain('city');
  });

  test('handles custom headers', () => {
    const data = [
      { name: 'John', age: 30 },
    ];
    
    const result = convertToCSV(data, { 
      headers: { name: 'Full Name', age: 'Age Years' } 
    });
    
    expect(result).toContain('Full Name');
    expect(result).toContain('Age Years');
  });

  test('escapes quotes in values', () => {
    const data = [
      { name: 'John "Jack" Doe', age: 30 },
    ];
    
    const result = convertToCSV(data);
    
    // Quotes should be doubled for CSV escaping
    expect(result).toContain('""');
  });

  test('handles null values', () => {
    const data = [
      { name: 'John', age: null },
    ];
    
    const result = convertToCSV(data);
    
    expect(result).toContain('John');
    expect(result).not.toContain('null');
  });

  test('formats date fields', () => {
    const data = [
      { date: '2024-01-15T10:30:00Z', name: 'Test' },
    ];
    
    const result = convertToCSV(data, { dateFields: ['date'] });
    
    expect(result).toContain('2024-01-15');
    expect(result).not.toContain('T10:30:00Z');
  });
});

describe('exportStockDataCSV', () => {
  // Mock document.createElement and URL.createObjectURL
  const mockLink = {
    href: '',
    download: '',
    click: jest.fn(),
  };
  
  beforeEach(() => {
    document.createElement = jest.fn().mockReturnValue(mockLink);
    document.body.appendChild = jest.fn();
    document.body.removeChild = jest.fn();
    URL.createObjectURL = jest.fn().mockReturnValue('blob:url');
    URL.revokeObjectURL = jest.fn();
    mockLink.click.mockClear();
  });

  test('exports stock data with correct filename', () => {
    const stockData = [
      { date: '2024-01-15', open: 150, high: 155, low: 148, close: 152, volume: 1000000 },
    ];
    
    exportStockDataCSV(stockData, 'AAPL');
    
    expect(mockLink.download).toContain('AAPL');
    expect(mockLink.download).toContain('prices');
    expect(mockLink.click).toHaveBeenCalled();
  });

  test('handles empty data', () => {
    const result = exportStockDataCSV([], 'AAPL');
    expect(result).toBe(false);
  });
});

describe('exportAnomaliesCSV', () => {
  const mockLink = {
    href: '',
    download: '',
    click: jest.fn(),
  };
  
  beforeEach(() => {
    document.createElement = jest.fn().mockReturnValue(mockLink);
    document.body.appendChild = jest.fn();
    document.body.removeChild = jest.fn();
    URL.createObjectURL = jest.fn().mockReturnValue('blob:url');
    URL.revokeObjectURL = jest.fn();
    mockLink.click.mockClear();
  });

  test('exports anomalies with correct filename', () => {
    const anomalies = [
      { date: '2024-01-15', type: 'price', score: 3.5, detection_method: 'zscore' },
    ];
    
    exportAnomaliesCSV(anomalies, 'AAPL');
    
    expect(mockLink.download).toContain('AAPL');
    expect(mockLink.download).toContain('anomalies');
    expect(mockLink.click).toHaveBeenCalled();
  });
});
