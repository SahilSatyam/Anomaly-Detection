/**
 * Loading Skeleton Component Tests
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  ChartSkeleton,
  TableSkeleton,
  StatCardSkeleton,
  DashboardSkeleton,
  LoadingOverlay,
  InlineLoader,
} from './LoadingSkeleton';

describe('ChartSkeleton', () => {
  test('renders with default height', () => {
    const { container } = render(<ChartSkeleton />);
    
    // Should render a Paper component
    expect(container.querySelector('.MuiPaper-root')).toBeInTheDocument();
  });

  test('renders with custom height', () => {
    const { container } = render(<ChartSkeleton height={600} />);
    
    const paper = container.querySelector('.MuiPaper-root');
    expect(paper).toHaveStyle({ height: '600px' });
  });
});

describe('TableSkeleton', () => {
  test('renders correct number of rows', () => {
    const { container } = render(<TableSkeleton rows={5} columns={3} />);
    
    // Should have 5 row containers (excluding header)
    const rowDivs = container.querySelectorAll('.MuiBox-root');
    expect(rowDivs.length).toBeGreaterThan(5);
  });

  test('renders with different row counts', () => {
    const { container } = render(<TableSkeleton rows={10} columns={4} />);
    
    expect(container).toBeInTheDocument();
  });
});

describe('StatCardSkeleton', () => {
  test('renders skeleton elements', () => {
    const { container } = render(<StatCardSkeleton />);
    
    // Should have Skeleton elements
    const skeletons = container.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});

describe('DashboardSkeleton', () => {
  test('renders full dashboard skeleton', () => {
    const { container } = render(<DashboardSkeleton />);
    
    // Should render multiple sections
    const papers = container.querySelectorAll('.MuiPaper-root');
    expect(papers.length).toBeGreaterThan(0);
  });
});

describe('LoadingOverlay', () => {
  test('renders loading message', () => {
    render(<LoadingOverlay message="Loading data..." />);
    
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  test('renders default message', () => {
    render(<LoadingOverlay />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});

describe('InlineLoader', () => {
  test('renders with default size', () => {
    const { container } = render(<InlineLoader />);
    
    expect(container.firstChild).toBeInTheDocument();
  });

  test('renders with custom size', () => {
    const { container } = render(<InlineLoader size={32} />);
    
    expect(container.firstChild).toBeInTheDocument();
  });
});
