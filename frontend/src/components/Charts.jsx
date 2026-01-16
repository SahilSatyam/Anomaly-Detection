/**
 * Enhanced Charts Component
 * 
 * Features:
 * - Candlestick chart with volume
 * - Anomaly markers/annotations on the chart
 * - Loading skeleton
 * - Responsive design
 */

import React, { useEffect, useRef, useMemo } from 'react';
import * as LightweightCharts from 'lightweight-charts';
import { Box, Paper, Typography, Chip, Tooltip } from '@mui/material';
import { ChartSkeleton } from './LoadingSkeleton';

const Charts = ({ data = [], anomalies = [], loading, symbol = '' }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const mainSeriesRef = useRef(null);

  // Process anomalies into markers
  const anomalyMarkers = useMemo(() => {
    if (!anomalies.length || !data.length) return [];
    
    // Create a map of dates to stock prices
    const priceByDate = {};
    data.forEach(item => {
      const dateKey = new Date(item.date).toISOString().split('T')[0];
      priceByDate[dateKey] = item;
    });

    return anomalies.map(anomaly => {
      const dateKey = new Date(anomaly.date).toISOString().split('T')[0];
      const priceData = priceByDate[dateKey];
      
      if (!priceData) return null;

      const timestamp = Math.floor(new Date(anomaly.date).getTime() / 1000);
      
      // Determine marker position and color based on anomaly type
      const isHighAnomaly = anomaly.score > 3;
      const isMediumAnomaly = anomaly.score > 2;
      
      return {
        time: timestamp,
        position: 'aboveBar',
        color: isHighAnomaly ? '#f44336' : isMediumAnomaly ? '#ff9800' : '#ffeb3b',
        shape: 'circle',
        text: `${anomaly.type || 'A'}`,
        size: isHighAnomaly ? 2 : 1,
        // Store additional data for tooltip
        anomalyData: anomaly,
      };
    }).filter(Boolean);
  }, [anomalies, data]);

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
          bottom: 0.25,
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
        bottom: 0.02,
      },
    });

    // Format and sort data for the chart
    const formattedData = data
      .map(item => {
        const timestamp = Math.floor(new Date(item.date).getTime() / 1000);
        return {
          time: timestamp,
          open: parseFloat(item.open),
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          close: parseFloat(item.close),
        };
      })
      .reduce((acc, curr) => {
        acc[curr.time] = curr;
        return acc;
      }, {});

    const sortedData = Object.values(formattedData).sort((a, b) => a.time - b.time);

    // Format volume data
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

    // Add anomaly markers
    if (anomalyMarkers.length > 0) {
      // Filter markers to only include valid times and sort them
      const validMarkers = anomalyMarkers
        .filter(marker => sortedData.some(d => d.time === marker.time))
        .sort((a, b) => a.time - b.time);
      
      if (validMarkers.length > 0) {
        mainSeries.setMarkers(validMarkers);
      }
    }

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

    // Store references
    chartRef.current = chart;
    mainSeriesRef.current = mainSeries;

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
  }, [data, loading, anomalyMarkers]);

  if (loading) {
    return <ChartSkeleton height={500} />;
  }

  if (!data.length) {
    return (
      <Paper sx={{ p: 2, bgcolor: '#1a1a1a', color: '#d1d4dc', width: '100%' }}>
        <Typography variant="body1">No chart data available.</Typography>
      </Paper>
    );
  }

  // Count anomalies by severity
  const anomalyCounts = anomalies.reduce((acc, a) => {
    if (a.score > 3) acc.high++;
    else if (a.score > 2) acc.medium++;
    else acc.low++;
    return acc;
  }, { high: 0, medium: 0, low: 0 });

  return (
    <Paper 
      sx={{ 
        p: 2, 
        bgcolor: '#1a1a1a',
        borderRadius: 2,
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        width: '100%',
        minWidth: '800px',
        height: '540px',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography 
          variant="h6" 
          sx={{ 
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: '1rem',
            fontWeight: 500,
          }}
        >
          Stock Price Trends {symbol && `- ${symbol}`}
        </Typography>
        
        {/* Anomaly Legend */}
        {anomalies.length > 0 && (
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', mr: 1 }}>
              Anomalies:
            </Typography>
            {anomalyCounts.high > 0 && (
              <Tooltip title="High severity anomalies (score > 3)">
                <Chip 
                  size="small" 
                  label={`${anomalyCounts.high} High`}
                  sx={{ 
                    bgcolor: '#f44336', 
                    color: 'white',
                    fontSize: '0.7rem',
                    height: 22,
                  }}
                />
              </Tooltip>
            )}
            {anomalyCounts.medium > 0 && (
              <Tooltip title="Medium severity anomalies (score 2-3)">
                <Chip 
                  size="small" 
                  label={`${anomalyCounts.medium} Med`}
                  sx={{ 
                    bgcolor: '#ff9800', 
                    color: 'black',
                    fontSize: '0.7rem',
                    height: 22,
                  }}
                />
              </Tooltip>
            )}
            {anomalyCounts.low > 0 && (
              <Tooltip title="Low severity anomalies (score < 2)">
                <Chip 
                  size="small" 
                  label={`${anomalyCounts.low} Low`}
                  sx={{ 
                    bgcolor: '#ffeb3b', 
                    color: 'black',
                    fontSize: '0.7rem',
                    height: 22,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        )}
      </Box>
      
      <Box 
        ref={chartContainerRef} 
        sx={{ 
          width: '100%',
          height: 'calc(100% - 40px)',
          '& canvas': {
            borderRadius: 1,
          }
        }} 
      />
    </Paper>
  );
};

export default Charts;