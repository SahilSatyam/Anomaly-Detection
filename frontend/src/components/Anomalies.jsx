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
} from '@mui/material';

const Anomalies = ({ anomalies = [], loading }) => {
  if (loading) {
    return <Typography>Loading anomalies...</Typography>;
  }

  if (!anomalies.length) {
    return <Typography>No anomalies detected in this period.</Typography>;
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
              <TableCell>{new Date(anomaly.date).toLocaleDateString()}</TableCell>
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

export default Anomalies; 