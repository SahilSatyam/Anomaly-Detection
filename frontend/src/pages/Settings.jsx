import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';

const Settings = () => {
  const [settings, setSettings] = useState({
    anomalyThreshold: 0.8,
    lookbackPeriod: 30,
    updateFrequency: 'daily',
  });

  const fetchSettings = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings');
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    try {
      await fetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Anomaly Detection Threshold"
              type="number"
              value={settings.anomalyThreshold}
              onChange={(e) => setSettings({ ...settings, anomalyThreshold: parseFloat(e.target.value) })}
              inputProps={{ step: 0.1, min: 0, max: 1 }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Lookback Period (days)"
              type="number"
              value={settings.lookbackPeriod}
              onChange={(e) => setSettings({ ...settings, lookbackPeriod: parseInt(e.target.value) })}
              inputProps={{ min: 1 }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Update Frequency</InputLabel>
              <Select
                value={settings.updateFrequency}
                label="Update Frequency"
                onChange={(e) => setSettings({ ...settings, updateFrequency: e.target.value })}
              >
                <MenuItem value="hourly">Hourly</MenuItem>
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Button variant="contained" onClick={handleSave}>
              Save Settings
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default Settings; 