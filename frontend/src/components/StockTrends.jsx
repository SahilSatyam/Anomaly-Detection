import React from 'react';
import { Box, CircularProgress } from '@mui/material';
import { createChart } from 'lightweight-charts';

const StockTrends = ({ data, loading }) => {
  const chartContainerRef = React.useRef();
  const chartRef = React.useRef();

  React.useEffect(() => {
    if (!data || loading) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#d9d9d9',
      },
      grid: {
        vertLines: { color: '#2e2e2e' },
        horzLines: { color: '#2e2e2e' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
    });

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Format data for the chart
    const chartData = data.map(item => ({
      time: item.date,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    // Set data
    candlestickSeries.setData(chartData);

    // Fit content
    chart.timeScale().fitContent();

    // Store chart reference
    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current.clientWidth,
      });
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, loading]);

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: 400,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      ref={chartContainerRef}
      sx={{
        width: '100%',
        height: 400,
      }}
    />
  );
};

export default StockTrends; 