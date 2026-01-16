/**
 * Historical Records Component
 * 
 * Displays stock price history in a table with:
 * - Skeleton loading states
 * - Color-coded changes
 * - Pagination support
 */

import React, { useState, useMemo } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  Box,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';

import { TableSkeleton } from './LoadingSkeleton';

/**
 * Format number with fixed decimals
 */
const formatPrice = (price) => {
  if (price === null || price === undefined) return 'N/A';
  return `$${parseFloat(price).toFixed(2)}`;
};

/**
 * Format volume with locale
 */
const formatVolume = (volume) => {
  if (volume === null || volume === undefined) return 'N/A';
  return parseInt(volume).toLocaleString();
};

/**
 * Calculate daily change
 */
const getDailyChange = (open, close) => {
  const change = close - open;
  const percentChange = (change / open) * 100;
  return {
    change,
    percentChange,
    isPositive: change > 0,
    isNegative: change < 0,
  };
};

const HistoricalRecords = ({ records = [], loading }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Sort records by date (most recent first)
  const sortedRecords = useMemo(() => {
    return [...records].sort((a, b) => new Date(b.date) - new Date(a.date));
  }, [records]);

  // Paginated records
  const paginatedRecords = useMemo(() => {
    const start = page * rowsPerPage;
    return sortedRecords.slice(start, start + rowsPerPage);
  }, [sortedRecords, page, rowsPerPage]);

  if (loading) {
    return <TableSkeleton rows={5} columns={7} />;
  }

  if (!records.length) {
    return (
      <Box 
        sx={{ 
          py: 4, 
          textAlign: 'center',
          color: 'text.secondary',
        }}
      >
        <Typography>No historical records available.</Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
          Select a stock and date range to view price history.
        </Typography>
      </Box>
    );
  }

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box>
      <TableContainer 
        component={Paper}
        sx={{ 
          bgcolor: 'transparent',
          boxShadow: 'none',
          maxHeight: 500,
        }}
      >
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Date</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">Open</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">High</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">Low</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">Close</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">Volume</TableCell>
              <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }} align="right">Change</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedRecords.map((record, index) => {
              const change = getDailyChange(record.open, record.close);
              
              return (
                <TableRow 
                  key={record.date || index}
                  sx={{
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  <TableCell>
                    {new Date(record.date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </TableCell>
                  
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                    {formatPrice(record.open)}
                  </TableCell>
                  
                  <TableCell 
                    align="right" 
                    sx={{ 
                      fontFamily: 'monospace',
                      color: 'success.light',
                    }}
                  >
                    {formatPrice(record.high)}
                  </TableCell>
                  
                  <TableCell 
                    align="right" 
                    sx={{ 
                      fontFamily: 'monospace',
                      color: 'error.light',
                    }}
                  >
                    {formatPrice(record.low)}
                  </TableCell>
                  
                  <TableCell 
                    align="right" 
                    sx={{ 
                      fontFamily: 'monospace',
                      fontWeight: 600,
                    }}
                  >
                    {formatPrice(record.close)}
                  </TableCell>
                  
                  <TableCell 
                    align="right" 
                    sx={{ 
                      fontFamily: 'monospace',
                      color: 'text.secondary',
                    }}
                  >
                    {formatVolume(record.volume)}
                  </TableCell>
                  
                  <TableCell align="right">
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'flex-end',
                        gap: 0.5,
                        color: change.isPositive 
                          ? 'success.main' 
                          : change.isNegative 
                            ? 'error.main' 
                            : 'text.secondary',
                      }}
                    >
                      {change.isPositive ? (
                        <TrendingUpIcon fontSize="small" />
                      ) : change.isNegative ? (
                        <TrendingDownIcon fontSize="small" />
                      ) : (
                        <TrendingFlatIcon fontSize="small" />
                      )}
                      <Typography 
                        variant="body2" 
                        component="span"
                        sx={{ fontFamily: 'monospace' }}
                      >
                        {change.isPositive ? '+' : ''}
                        {change.percentChange.toFixed(2)}%
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={sortedRecords.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        sx={{
          '.MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows': {
            color: 'text.secondary',
          },
        }}
      />
    </Box>
  );
};

export default HistoricalRecords;