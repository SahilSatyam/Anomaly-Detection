/**
 * Anomalies Component
 * 
 * Displays detected anomalies in a table with:
 * - Skeleton loading states
 * - Severity-based styling
 * - Verification status
 */

import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Box,
  Tooltip,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { TableSkeleton } from './LoadingSkeleton';

/**
 * Get severity level based on anomaly score
 */
const getSeverity = (score) => {
  if (score >= 3) return { level: 'high', color: 'error', icon: <ErrorIcon fontSize="small" /> };
  if (score >= 2) return { level: 'medium', color: 'warning', icon: <WarningIcon fontSize="small" /> };
  return { level: 'low', color: 'info', icon: <InfoIcon fontSize="small" /> };
};

/**
 * Format detection method for display
 */
const formatMethod = (method) => {
  if (!method) return 'Unknown';
  return method
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
};

const Anomalies = ({ anomalies = [], loading }) => {
  if (loading) {
    return <TableSkeleton rows={5} columns={5} />;
  }

  if (!anomalies.length) {
    return (
      <Box 
        sx={{ 
          py: 4, 
          textAlign: 'center',
          color: 'text.secondary',
        }}
      >
        <CheckCircleIcon sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
        <Typography>No anomalies detected in this period.</Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
          This is a good sign! Your data appears normal.
        </Typography>
      </Box>
    );
  }

  // Sort anomalies by date (most recent first)
  const sortedAnomalies = [...anomalies].sort((a, b) => 
    new Date(b.date) - new Date(a.date)
  );

  return (
    <TableContainer 
      component={Paper}
      sx={{ 
        bgcolor: 'transparent',
        boxShadow: 'none',
        maxHeight: 400,
      }}
    >
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Date</TableCell>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Severity</TableCell>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Type</TableCell>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Score</TableCell>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Method</TableCell>
            <TableCell sx={{ bgcolor: 'background.paper', fontWeight: 600 }}>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedAnomalies.map((anomaly, index) => {
            const severity = getSeverity(anomaly.score);
            const isVerified = anomaly.is_verified;
            
            return (
              <TableRow 
                key={anomaly.id || index}
                sx={{
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                  },
                  // Highlight high severity
                  ...(severity.level === 'high' && {
                    bgcolor: 'rgba(244, 67, 54, 0.1)',
                  }),
                }}
              >
                <TableCell>
                  {new Date(anomaly.date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </TableCell>
                
                <TableCell>
                  <Tooltip title={`Severity: ${severity.level}`}>
                    <Chip
                      icon={severity.icon}
                      label={severity.level.toUpperCase()}
                      color={severity.color}
                      size="small"
                      variant="filled"
                      sx={{ 
                        fontWeight: 600,
                        fontSize: '0.7rem',
                      }}
                    />
                  </Tooltip>
                </TableCell>
                
                <TableCell>
                  <Chip
                    label={anomaly.type || anomaly.anomaly_type || 'Unknown'}
                    color={anomaly.type === 'price' ? 'error' : 'warning'}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                
                <TableCell>
                  <Tooltip title={`Raw score: ${anomaly.score}`}>
                    <Typography 
                      variant="body2"
                      sx={{ 
                        fontWeight: severity.level === 'high' ? 700 : 400,
                        color: severity.level === 'high' ? 'error.main' : 'inherit',
                      }}
                    >
                      {anomaly.score?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Tooltip>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {formatMethod(anomaly.detection_method)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Chip
                    label={isVerified ? 'Verified' : 'Pending'}
                    color={isVerified ? 'success' : 'default'}
                    size="small"
                    variant={isVerified ? 'filled' : 'outlined'}
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default Anomalies;