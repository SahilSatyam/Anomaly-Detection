import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Chip,
} from '@mui/material';

const AnomalyList = ({ anomalies, loading }) => {
  if (loading) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography>Loading anomalies...</Typography>
      </Box>
    );
  }

  if (!anomalies || anomalies.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography>No anomalies detected in the selected period.</Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Date</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Score</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {anomalies.map((anomaly) => (
            <TableRow key={anomaly.id}>
              <TableCell>{new Date(anomaly.timestamp).toLocaleDateString()}</TableCell>
              <TableCell>
                <Chip
                  label={anomaly.type}
                  color={anomaly.type === 'price' ? 'error' : 'warning'}
                  size="small"
                />
              </TableCell>
              <TableCell>{anomaly.score.toFixed(2)}</TableCell>
              <TableCell>{anomaly.description}</TableCell>
              <TableCell>
                <Chip
                  label={anomaly.status}
                  color={anomaly.status === 'confirmed' ? 'success' : 'default'}
                  size="small"
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default AnomalyList; 