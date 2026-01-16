/**
 * Dashboard Page
 * 
 * Main dashboard view with:
 * - Stock selection and date range picker
 * - Date validation
 * - Real-time updates with polling
 * - Skeleton loading states
 * - Export functionality
 * - Anomaly visualization on charts
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box,
  TextField,
  Button,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Chip,
  Collapse,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import StockSelector from '../components/StockSelector';
import Charts from '../components/Charts';
import Anomalies from '../components/Anomalies';
import HistoricalRecords from '../components/HistoricalRecords';
import ExportToolbar from '../components/ExportToolbar';
import { 
  DashboardSkeleton, 
  TableSkeleton,
  InlineLoader 
} from '../components/LoadingSkeleton';

import { validateDateRange, getDatePresets, formatDate } from '../utils/dateValidation';
import { useStockData, useHealthCheck, useLocalStorage } from '../hooks/useDataFetching';

const Dashboard = () => {
  // Persisted preferences
  const [preferences, setPreferences] = useLocalStorage('dashboard_preferences', {
    autoRefresh: false,
    refreshInterval: 60000,
    showHistoricalRecords: false,
  });

  // Date state
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [dateError, setDateError] = useState(null);

  // Stock state
  const [selectedStock, setSelectedStock] = useState('AAPL');
  
  // UI state
  const [showHistorical, setShowHistorical] = useState(preferences.showHistoricalRecords);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Data fetching with the custom hook
  const {
    stockData,
    anomalies,
    loading,
    error,
    lastUpdated,
    refetch,
    silentRefresh,
  } = useStockData(selectedStock, startDate, endDate, {
    autoRefresh: preferences.autoRefresh,
    refreshInterval: preferences.refreshInterval,
    enabled: true,
  });

  // Health check
  const { isHealthy, isPolling: isHealthPolling } = useHealthCheck(30000);

  // Date presets
  const datePresets = useMemo(() => getDatePresets(), []);

  // Validate dates when they change
  useEffect(() => {
    const validation = validateDateRange(startDate, endDate);
    setDateError(validation.isValid ? null : validation.error);
  }, [startDate, endDate]);

  // Handle date preset selection
  const handlePresetSelect = useCallback((preset) => {
    const { start, end } = preset.getRange();
    setStartDate(start);
    setEndDate(end);
  }, []);

  // Handle start date change with validation
  const handleStartDateChange = (date) => {
    setStartDate(date);
    // Auto-adjust end date if needed
    if (date && endDate && date > endDate) {
      setEndDate(date);
    }
  };

  // Handle end date change with validation
  const handleEndDateChange = (date) => {
    setEndDate(date);
    // Auto-adjust start date if needed
    if (date && startDate && date < startDate) {
      setStartDate(date);
    }
  };

  // Toggle auto-refresh
  const handleAutoRefreshToggle = (event) => {
    const newValue = event.target.checked;
    setPreferences(prev => ({ ...prev, autoRefresh: newValue }));
    
    setSnackbar({
      open: true,
      message: newValue ? 'Auto-refresh enabled (1 minute interval)' : 'Auto-refresh disabled',
      severity: 'info',
    });
  };

  // Manual refresh
  const handleManualRefresh = () => {
    if (!dateError) {
      refetch();
      setSnackbar({
        open: true,
        message: 'Data refreshed',
        severity: 'success',
      });
    }
  };

  // Toggle historical records visibility
  const handleToggleHistorical = () => {
    const newValue = !showHistorical;
    setShowHistorical(newValue);
    setPreferences(prev => ({ ...prev, showHistoricalRecords: newValue }));
  };

  // Show error snackbar
  useEffect(() => {
    if (error) {
      setSnackbar({
        open: true,
        message: error,
        severity: 'error',
      });
    }
  }, [error]);

  // Initial loading state
  if (loading && !stockData.length) {
    return (
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <DashboardSkeleton />
      </LocalizationProvider>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Stock Anomaly Detection Dashboard
          </Typography>
          
          {/* Status indicators */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* API Health */}
            <Tooltip title={isHealthy ? 'API is healthy' : 'API connection issue'}>
              <Chip
                size="small"
                icon={isHealthy ? <CheckCircleIcon /> : <ErrorIcon />}
                label={isHealthy ? 'Online' : 'Offline'}
                color={isHealthy ? 'success' : 'error'}
                variant="outlined"
              />
            </Tooltip>
            
            {/* Last updated */}
            {lastUpdated && (
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Updated: {formatDate(lastUpdated, 'short')} {lastUpdated.toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </Box>
        
        {/* Controls Panel */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            {/* Stock Selector */}
            <Grid item xs={12} sm={2}>
              <StockSelector
                value={selectedStock}
                onChange={setSelectedStock}
                disabled={loading}
              />
            </Grid>
            
            {/* Date Range */}
            <Grid item xs={12} sm={2}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={handleStartDateChange}
                maxDate={endDate || new Date()}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    size: 'small',
                    error: !!dateError,
                  }
                }}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={handleEndDateChange}
                minDate={startDate}
                maxDate={new Date()}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    size: 'small',
                    error: !!dateError,
                  }
                }}
                disabled={loading}
              />
            </Grid>
            
            {/* Date Presets */}
            <Grid item xs={12} sm={2}>
              <TextField
                select
                label="Quick Select"
                size="small"
                fullWidth
                SelectProps={{ native: true }}
                onChange={(e) => {
                  const preset = datePresets.find(p => p.value === e.target.value);
                  if (preset) handlePresetSelect(preset);
                }}
                disabled={loading}
              >
                <option value="">Custom</option>
                {datePresets.map(preset => (
                  <option key={preset.value} value={preset.value}>
                    {preset.label}
                  </option>
                ))}
              </TextField>
            </Grid>
            
            {/* Actions */}
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', justifyContent: 'flex-end' }}>
                {/* Auto-refresh toggle */}
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.autoRefresh}
                      onChange={handleAutoRefreshToggle}
                      size="small"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AutorenewIcon 
                        fontSize="small" 
                        sx={{ 
                          animation: preferences.autoRefresh ? 'spin 2s linear infinite' : 'none',
                          '@keyframes spin': {
                            '0%': { transform: 'rotate(0deg)' },
                            '100%': { transform: 'rotate(360deg)' },
                          },
                        }} 
                      />
                      <Typography variant="caption">Auto</Typography>
                    </Box>
                  }
                />
                
                {/* Refresh button */}
                <Tooltip title="Refresh data">
                  <span>
                    <IconButton
                      onClick={handleManualRefresh}
                      disabled={loading || !!dateError}
                      color="primary"
                    >
                      {loading ? <InlineLoader size={20} /> : <RefreshIcon />}
                    </IconButton>
                  </span>
                </Tooltip>
                
                {/* Export */}
                <ExportToolbar
                  stockData={stockData}
                  anomalies={anomalies}
                  symbol={selectedStock}
                  dateRange={{
                    start: formatDate(startDate, 'iso'),
                    end: formatDate(endDate, 'iso'),
                  }}
                  disabled={loading}
                />
              </Box>
            </Grid>
          </Grid>
          
          {/* Date validation error */}
          {dateError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {dateError}
            </Alert>
          )}
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
            <Button 
              size="small" 
              onClick={handleManualRefresh} 
              sx={{ ml: 2 }}
            >
              Retry
            </Button>
          </Alert>
        )}

        {/* Main Content */}
        <Grid container spacing={3}>
          {/* Chart with anomaly markers */}
          <Grid item xs={12}>
            <Charts 
              data={stockData} 
              anomalies={anomalies}
              loading={loading} 
              symbol={selectedStock}
            />
          </Grid>
          
          {/* Anomalies Section */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Detected Anomalies
                  {anomalies.length > 0 && (
                    <Chip 
                      label={anomalies.length} 
                      size="small" 
                      color="warning"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Typography>
              </Box>
              
              {loading && !anomalies.length ? (
                <TableSkeleton rows={3} columns={5} />
              ) : (
                <Anomalies anomalies={anomalies} loading={false} />
              )}
            </Paper>
          </Grid>

          {/* Historical Records (collapsible) */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Box 
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  cursor: 'pointer',
                }}
                onClick={handleToggleHistorical}
              >
                <Typography variant="h6">
                  Historical Records
                  {stockData.length > 0 && (
                    <Chip 
                      label={stockData.length} 
                      size="small" 
                      sx={{ ml: 1 }}
                    />
                  )}
                </Typography>
                <IconButton size="small">
                  {showHistorical ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              
              <Collapse in={showHistorical}>
                <Box sx={{ mt: 2 }}>
                  {loading && !stockData.length ? (
                    <TableSkeleton rows={5} columns={6} />
                  ) : (
                    <HistoricalRecords records={stockData} loading={false} />
                  )}
                </Box>
              </Collapse>
            </Paper>
          </Grid>
        </Grid>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert 
            onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
            severity={snackbar.severity}
            variant="filled"
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </LocalizationProvider>
  );
};

export default Dashboard;