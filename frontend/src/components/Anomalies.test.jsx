/**
 * Anomalies Component Tests
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import Anomalies from './Anomalies';

// Mock the LoadingSkeleton component
jest.mock('./LoadingSkeleton', () => ({
  TableSkeleton: () => <div data-testid="table-skeleton">Loading...</div>,
}));

describe('Anomalies Component', () => {
  const mockAnomalies = [
    {
      id: 1,
      date: '2024-01-15',
      type: 'price',
      anomaly_type: 'price',
      score: 3.5,
      detection_method: 'zscore',
      is_verified: false,
    },
    {
      id: 2,
      date: '2024-01-10',
      type: 'volume',
      anomaly_type: 'volume',
      score: 2.1,
      detection_method: 'isolation_forest',
      is_verified: true,
    },
  ];

  test('renders loading skeleton when loading', () => {
    render(<Anomalies anomalies={[]} loading={true} />);
    
    expect(screen.getByTestId('table-skeleton')).toBeInTheDocument();
  });

  test('renders empty state when no anomalies', () => {
    render(<Anomalies anomalies={[]} loading={false} />);
    
    expect(screen.getByText(/no anomalies detected/i)).toBeInTheDocument();
  });

  test('renders anomalies table when data provided', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    // Check table headers
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Severity')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Score')).toBeInTheDocument();
  });

  test('displays anomaly data correctly', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    // Check for anomaly type chips
    expect(screen.getByText('price')).toBeInTheDocument();
    expect(screen.getByText('volume')).toBeInTheDocument();
    
    // Check for scores
    expect(screen.getByText('3.50')).toBeInTheDocument();
    expect(screen.getByText('2.10')).toBeInTheDocument();
  });

  test('shows verification status', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  test('displays severity badges based on score', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    // High severity (score > 3)
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    // Medium severity (score 2-3)
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  test('formats detection method correctly', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    // isolation_forest should be formatted as "Isolation Forest"
    expect(screen.getByText('Isolation Forest')).toBeInTheDocument();
  });

  test('sorts anomalies by date (newest first)', () => {
    render(<Anomalies anomalies={mockAnomalies} loading={false} />);
    
    const rows = screen.getAllByRole('row');
    // First row is header, second row should be Jan 15 (newest)
    expect(rows[1]).toHaveTextContent('Jan 15');
  });

  test('handles anomalies with missing fields', () => {
    const incompleteAnomalies = [
      {
        id: 1,
        date: '2024-01-15',
        score: 2.5,
      },
    ];
    
    render(<Anomalies anomalies={incompleteAnomalies} loading={false} />);
    
    // Should render without crashing
    expect(screen.getByText('2.50')).toBeInTheDocument();
  });
});
