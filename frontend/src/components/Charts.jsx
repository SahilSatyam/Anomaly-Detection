import React, { useEffect, useRef } from 'react';
import * as LightweightCharts from 'lightweight-charts';
import { Box, Paper, Typography } from '@mui/material';

const Charts = ({ data = [], loading }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!data.length || loading || !chartContainerRef.current) return;

    const container = chartContainerRef.current;
    const width = Math.max(container.clientWidth, 800);

    // Create chart instance with modern styling
    const chart = LightweightCharts.createChart(container, {
      width: width,
      height: 450,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: 'rgba(255, 255, 255, 0.5)',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
        vertLine: {
          width: 1,
          color: 'rgba(224, 227, 235, 0.4)',
          style: 0,
        },
        horzLine: {
          width: 1,
          color: 'rgba(224, 227, 235, 0.4)',
          style: 0,
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(197, 203, 206, 0.2)',
        textColor: 'rgba(255, 255, 255, 0.5)',
        scaleMargins: {
          top: 0.2,
          bottom: 0.2,
        },
        visible: true,
        borderVisible: true,
        alignLabels: true,
      },
      timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.2)',
        textColor: 'rgba(255, 255, 255, 0.5)',
        timeVisible: true,
        secondsVisible: false,
        borderVisible: true,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    // Create candlestick series with modern colors
    const mainSeries = chart.addCandlestickSeries({
      upColor: 'rgba(8, 153, 129, 0.9)',
      downColor: 'rgba(242, 54, 69, 0.9)',
      borderUpColor: 'rgba(8, 153, 129, 0.9)',
      borderDownColor: 'rgba(242, 54, 69, 0.9)',
      wickUpColor: 'rgba(154, 242, 227, 0.9)',
      wickDownColor: 'rgba(212, 142, 148, 0.9)',
    });

    // Create volume series with modern styling
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0.1,
      },
    });

    // Format and sort data for the chart
    const formattedData = data
      .map(item => {
        // Convert date string to timestamp (in seconds)
        const timestamp = Math.floor(new Date(item.date).getTime() / 1000);
        return {
          time: timestamp,
          open: parseFloat(item.open),
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          close: parseFloat(item.close),
        };
      })
      // Remove duplicates by keeping the latest entry for each timestamp
      .reduce((acc, curr) => {
        acc[curr.time] = curr;
        return acc;
      }, {});

    // Convert back to array and sort by timestamp
    const sortedData = Object.values(formattedData).sort((a, b) => a.time - b.time);

    // Format volume data with the same timestamp handling
    const volumeData = data
      .map(item => {
        const timestamp = Math.floor(new Date(item.date).getTime() / 1000);
        return {
          time: timestamp,
          value: parseFloat(item.volume),
          color: parseFloat(item.close) >= parseFloat(item.open) 
            ? 'rgba(8, 153, 129, 0.3)'
            : 'rgba(242, 54, 69, 0.3)',
        };
      })
      .reduce((acc, curr) => {
        acc[curr.time] = curr;
        return acc;
      }, {});

    const sortedVolumeData = Object.values(volumeData).sort((a, b) => a.time - b.time);

    // Set the data
    mainSeries.setData(sortedData);
    volumeSeries.setData(sortedVolumeData);

    // Set visible range to last 30 data points
    const timeScale = chart.timeScale();
    const dataLength = sortedData.length;
    if (dataLength > 30) {
      timeScale.setVisibleRange({
        from: sortedData[dataLength - 30].time,
        to: sortedData[dataLength - 1].time,
      });
    } else {
      timeScale.fitContent();
    }

    // Store chart reference
    chartRef.current = chart;

    // Handle resize with debouncing
    let timeoutId;
    const handleResize = () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      timeoutId = setTimeout(() => {
        if (chartRef.current && container) {
          const newWidth = Math.max(container.clientWidth, 800);
          chartRef.current.applyOptions({
            width: newWidth,
            height: 450,
          });
          chartRef.current.timeScale().fitContent();
        }
      }, 100);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, loading]);

  if (loading) {
    return (
      <Paper sx={{ p: 2, bgcolor: '#1a1a1a', color: '#d1d4dc', width: '100%' }}>
        <Typography variant="body1">Loading chart data...</Typography>
      </Paper>
    );
  }

  if (!data.length) {
    return (
      <Paper sx={{ p: 2, bgcolor: '#1a1a1a', color: '#d1d4dc', width: '100%' }}>
        <Typography variant="body1">No chart data available.</Typography>
      </Paper>
    );
  }

  return (
    <Paper 
      sx={{ 
        p: 2, 
        bgcolor: '#1a1a1a',
        borderRadius: 2,
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        width: '100%',
        minWidth: '800px',
        height: '500px',
        overflow: 'hidden',
      }}
    >
      <Typography 
        variant="h6" 
        sx={{ 
          color: 'rgba(255, 255, 255, 0.7)',
          mb: 1,
          fontSize: '1rem',
          fontWeight: 500,
        }}
      >
        Stock Price Trends
      </Typography>
      <Box 
        ref={chartContainerRef} 
        sx={{ 
          width: '100%',
          height: '100%',
          '& canvas': {
            borderRadius: 1,
          }
        }} 
      />
    </Paper>
  );
};

export default Charts; 