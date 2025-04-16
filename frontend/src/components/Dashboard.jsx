import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import StockTrends from './StockTrends';
import AnomalyList from './AnomalyList';

const Dashboard = () => {
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [selectedStock, setSelectedStock] = useState('');
  const [stocks, setStocks] = useState([]);
  const [stockData, setStockData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStocks();
  }, []);

  const fetchStocks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/stocks');
      const data = await response.json();
      setStocks(data.data);
      if (data.data.length > 0) {
        setSelectedStock(data.data[0].symbol);
      }
    } catch (error) {
      console.error('Error fetching stocks:', error);
      setError('Failed to fetch available stocks');
    }
  };

  const fetchData = async () => {
    if (!selectedStock) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [stockResponse, anomaliesResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/stock-data?symbol=${selectedStock}&start=${startDate.toISOString()}&end=${endDate.toISOString()}`),
        fetch(`http://localhost:8000/api/anomalies?symbol=${selectedStock}&start=${startDate.toISOString()}&end=${endDate.toISOString()}`)
      ]);
      
      const stockData = await stockResponse.json();
      const anomaliesData = await anomaliesResponse.json();
      
      setStockData(stockData.data);
      setAnomalies(anomaliesData.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStock) {
      fetchData();
    }
  }, [selectedStock]);

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Stock Anomaly Detection Dashboard
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Stock</InputLabel>
                <Select
                  value={selectedStock}
                  label="Stock"
                  onChange={(e) => setSelectedStock(e.target.value)}
                >
                  {stocks.map((stock) => (
                    <MenuItem key={stock.symbol} value={stock.symbol}>
                      {stock.symbol} - {stock.company_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant="contained"
                onClick={fetchData}
                disabled={loading}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Update Data'}
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
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Stock Price Trends
              </Typography>
              <StockTrends data={stockData} loading={loading} />
            </Paper>
          </Grid>
          
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Detected Anomalies
              </Typography>
              <AnomalyList anomalies={anomalies} loading={loading} />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

export default Dashboard; 