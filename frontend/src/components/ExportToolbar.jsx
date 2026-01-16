/**
 * Export Toolbar Component
 * 
 * Provides buttons to export data in various formats (CSV, PDF).
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import TableChartIcon from '@mui/icons-material/TableChart';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import AssessmentIcon from '@mui/icons-material/Assessment';
import DescriptionIcon from '@mui/icons-material/Description';

import {
  exportStockDataCSV,
  exportAnomaliesCSV,
  generatePDFReport,
} from '../utils/exportData';

const ExportToolbar = ({ 
  stockData = [], 
  anomalies = [], 
  symbol = '',
  dateRange = {},
  disabled = false,
}) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [exporting, setExporting] = useState(false);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExport = async (type) => {
    setExporting(true);
    handleClose();

    // Small delay to show loading state
    await new Promise(resolve => setTimeout(resolve, 100));

    try {
      switch (type) {
        case 'stock-csv':
          exportStockDataCSV(stockData, symbol);
          break;
        case 'anomalies-csv':
          exportAnomaliesCSV(anomalies, symbol);
          break;
        case 'all-csv':
          if (stockData.length) exportStockDataCSV(stockData, symbol);
          if (anomalies.length) {
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 500));
            exportAnomaliesCSV(anomalies, symbol);
          }
          break;
        case 'pdf':
          generatePDFReport({
            stockData,
            anomalies,
            symbol,
            dateRange,
          }, `Stock Analysis Report - ${symbol}`);
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  const hasData = stockData.length > 0 || anomalies.length > 0;

  return (
    <Box>
      <Tooltip title={!hasData ? 'No data to export' : 'Export data'}>
        <span>
          <Button
            variant="outlined"
            startIcon={exporting ? <CircularProgress size={18} /> : <DownloadIcon />}
            onClick={handleClick}
            disabled={disabled || !hasData || exporting}
            sx={{
              borderColor: 'rgba(144, 202, 249, 0.5)',
              color: 'rgba(144, 202, 249, 0.9)',
              '&:hover': {
                borderColor: '#90caf9',
                bgcolor: 'rgba(144, 202, 249, 0.1)',
              },
              '&.Mui-disabled': {
                borderColor: 'rgba(255, 255, 255, 0.12)',
                color: 'rgba(255, 255, 255, 0.3)',
              },
            }}
          >
            {exporting ? 'Exporting...' : 'Export'}
          </Button>
        </span>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            bgcolor: '#2d2d2d',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            '& .MuiMenuItem-root': {
              '&:hover': {
                bgcolor: 'rgba(144, 202, 249, 0.1)',
              },
            },
          },
        }}
      >
        <MenuItem 
          onClick={() => handleExport('stock-csv')}
          disabled={!stockData.length}
        >
          <ListItemIcon>
            <TableChartIcon fontSize="small" sx={{ color: '#4caf50' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Stock Data (CSV)" 
            secondary={`${stockData.length} records`}
          />
        </MenuItem>

        <MenuItem 
          onClick={() => handleExport('anomalies-csv')}
          disabled={!anomalies.length}
        >
          <ListItemIcon>
            <AssessmentIcon fontSize="small" sx={{ color: '#ff9800' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Anomalies (CSV)" 
            secondary={`${anomalies.length} anomalies`}
          />
        </MenuItem>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        <MenuItem 
          onClick={() => handleExport('all-csv')}
          disabled={!hasData}
        >
          <ListItemIcon>
            <DescriptionIcon fontSize="small" sx={{ color: '#2196f3' }} />
          </ListItemIcon>
          <ListItemText primary="All Data (CSV)" secondary="Download both files" />
        </MenuItem>

        <MenuItem onClick={() => handleExport('pdf')}>
          <ListItemIcon>
            <PictureAsPdfIcon fontSize="small" sx={{ color: '#f44336' }} />
          </ListItemIcon>
          <ListItemText primary="PDF Report" secondary="Print-ready format" />
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ExportToolbar;
