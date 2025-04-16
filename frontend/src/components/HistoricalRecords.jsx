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
} from '@mui/material';

const HistoricalRecords = ({ records = [], loading }) => {
  if (loading) {
    return <Typography>Loading historical records...</Typography>;
  }

  if (!records.length) {
    return <Typography>No historical records available.</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Date</TableCell>
            <TableCell>Open</TableCell>
            <TableCell>High</TableCell>
            <TableCell>Low</TableCell>
            <TableCell>Close</TableCell>
            <TableCell>Volume</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((record) => (
            <TableRow key={record.date}>
              <TableCell>{new Date(record.date).toLocaleDateString()}</TableCell>
              <TableCell>{record.open.toFixed(2)}</TableCell>
              <TableCell>{record.high.toFixed(2)}</TableCell>
              <TableCell>{record.low.toFixed(2)}</TableCell>
              <TableCell>{record.close.toFixed(2)}</TableCell>
              <TableCell>{record.volume.toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default HistoricalRecords; 