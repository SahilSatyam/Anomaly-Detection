import React, { useState, useEffect, useCallback } from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box,
  TextField,
  Button,
  CircularProgress
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import StockTrends from '../components/StockTrends';
import Anomalies from '../components/Anomalies';
import HistoricalRecords from '../components/HistoricalRecords';
import Charts from '../components/Charts';
import StockSelector from '../components/StockSelector';

const Dashboard = () => {
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [selectedStock, setSelectedStock] = useState('AAPL');
  const [stockData, setStockData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStockData = useCallback(async () => {
    if (!selectedStock) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [stockResponse, anomaliesResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/stock-data?symbol=${selectedStock}&start=${startDate.toISOString()}&end=${endDate.toISOString()}`),
        fetch(`http://localhost:8000/api/anomalies?symbol=${selectedStock}&start=${startDate.toISOString()}&end=${endDate.toISOString()}`)
      ]);
      
      if (!stockResponse.ok || !anomaliesResponse.ok) {
        throw new Error('Failed to fetch data');
      }

      const stockData = await stockResponse.json();
      const anomaliesData = await anomaliesResponse.json();
      
      setStockData(stockData.data || []);
      setAnomalies(anomaliesData.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [selectedStock, startDate, endDate]);

  useEffect(() => {
    if (selectedStock) {
      fetchStockData();
    }
  }, [selectedStock, fetchStockData]);

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Stock Anomaly Detection Dashboard
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <StockSelector
                value={selectedStock}
                onChange={setSelectedStock}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant="contained"
                onClick={fetchStockData}
                disabled={loading || !selectedStock}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'UPDATE DATA'}
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {error && (
          <Paper sx={{ p: 2, mb: 3, bgcolor: 'error.light' }}>
            <Typography color="error">{error}</Typography>
          </Paper>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Charts data={stockData} loading={loading} />
          </Grid>
          
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Detected Anomalies
              </Typography>
              <Anomalies anomalies={anomalies} loading={loading} />
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Historical Records
              </Typography>
              <HistoricalRecords records={stockData} loading={loading} />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

export default Dashboard; 