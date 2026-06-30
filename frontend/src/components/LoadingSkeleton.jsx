/**
 * Loading Skeleton Components
 * 
 * Provides shimmer/skeleton loading states for various components.
 */

import React from 'react';
import { Box, Skeleton, Paper, Grid } from '@mui/material';

/**
 * Shimmer animation styles
 */
const shimmerKeyframes = `
  @keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
  }
`;

/**
 * Chart skeleton loader
 */
export const ChartSkeleton = ({ height = 450 }) => (
  <Paper 
    sx={{ 
      p: 2, 
      bgcolor: '#1a1a1a',
      borderRadius: 2,
      height: height,
      overflow: 'hidden',
    }}
  >
    <style>{shimmerKeyframes}</style>
    <Skeleton 
      variant="text" 
      width="30%" 
      height={28}
      sx={{ bgcolor: 'rgba(255,255,255,0.1)', mb: 2 }}
    />
    <Box sx={{ display: 'flex', alignItems: 'flex-end', height: 'calc(100% - 60px)', gap: 0.5 }}>
      {Array.from({ length: 50 }).map((_, i) => (
        <Skeleton
          key={i}
          variant="rectangular"
          width="2%"
          height={`${20 + Math.random() * 70}%`}
          sx={{ 
            bgcolor: 'rgba(255,255,255,0.08)',
            animation: 'shimmer 1.5s infinite',
            animationDelay: `${i * 30}ms`,
            background: 'linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%)',
            backgroundSize: '200px 100%',
          }}
        />
      ))}
    </Box>
    <Skeleton 
      variant="rectangular" 
      width="100%" 
      height={20}
      sx={{ bgcolor: 'rgba(255,255,255,0.05)', mt: 1 }}
    />
  </Paper>
);

/**
 * Table skeleton loader
 */
export const TableSkeleton = ({ rows = 5, columns = 5 }) => (
  <Box>
    <style>{shimmerKeyframes}</style>
    {/* Header */}
    <Box sx={{ display: 'flex', gap: 2, mb: 1, pb: 1, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={`header-${i}`}
          variant="text"
          width={`${100 / columns}%`}
          height={24}
          sx={{ bgcolor: 'rgba(255,255,255,0.15)' }}
        />
      ))}
    </Box>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <Box 
        key={`row-${rowIndex}`}
        sx={{ 
          display: 'flex', 
          gap: 2, 
          py: 1.5,
          borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}
      >
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton
            key={`cell-${rowIndex}-${colIndex}`}
            variant="text"
            width={`${100 / columns}%`}
            height={20}
            sx={{ 
              bgcolor: 'rgba(255,255,255,0.08)',
              animation: 'shimmer 1.5s infinite',
              animationDelay: `${(rowIndex * columns + colIndex) * 50}ms`,
              background: 'linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%)',
              backgroundSize: '200px 100%',
            }}
          />
        ))}
      </Box>
    ))}
  </Box>
);

/**
 * Stats card skeleton
 */
export const StatCardSkeleton = () => (
  <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
    <style>{shimmerKeyframes}</style>
    <Skeleton 
      variant="text" 
      width="40%" 
      height={20}
      sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}
    />
    <Skeleton 
      variant="text" 
      width="70%" 
      height={40}
      sx={{ 
        bgcolor: 'rgba(255,255,255,0.15)',
        mt: 1,
        animation: 'shimmer 1.5s infinite',
        background: 'linear-gradient(90deg, rgba(255,255,255,0.1) 25%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 75%)',
        backgroundSize: '200px 100%',
      }}
    />
    <Skeleton 
      variant="text" 
      width="50%" 
      height={16}
      sx={{ bgcolor: 'rgba(255,255,255,0.05)', mt: 1 }}
    />
  </Paper>
);

/**
 * Dashboard skeleton loader - full page
 */
export const DashboardSkeleton = () => (
  <Box sx={{ p: 3 }}>
    <style>{shimmerKeyframes}</style>
    {/* Header */}
    <Skeleton 
      variant="text" 
      width="40%" 
      height={48}
      sx={{ bgcolor: 'rgba(255,255,255,0.1)', mb: 2 }}
    />
    
    {/* Controls */}
    <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
      <Grid container spacing={2}>
        {[1, 2, 3, 4].map((i) => (
          <Grid size={{ xs: 12, sm: 3 }} key={i}>
            <Skeleton 
              variant="rectangular" 
              height={56}
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.1)',
                borderRadius: 1,
              }}
            />
          </Grid>
        ))}
      </Grid>
    </Paper>

    {/* Chart */}
    <Box sx={{ mb: 3 }}>
      <ChartSkeleton />
    </Box>

    {/* Stats */}
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {[1, 2, 3, 4].map((i) => (
        <Grid size={{ xs: 12, sm: 3 }} key={i}>
          <StatCardSkeleton />
        </Grid>
      ))}
    </Grid>

    {/* Table */}
    <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
      <Skeleton 
        variant="text" 
        width="20%" 
        height={32}
        sx={{ bgcolor: 'rgba(255,255,255,0.1)', mb: 2 }}
      />
      <TableSkeleton rows={5} columns={5} />
    </Paper>
  </Box>
);

/**
 * Generic loading overlay
 */
export const LoadingOverlay = ({ message = 'Loading...' }) => (
  <Box
    sx={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: 'rgba(0,0,0,0.7)',
      zIndex: 1000,
      borderRadius: 'inherit',
    }}
  >
    <Box
      sx={{
        width: 40,
        height: 40,
        border: '3px solid rgba(255,255,255,0.1)',
        borderTop: '3px solid #90caf9',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        '@keyframes spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      }}
    />
    <Box sx={{ color: 'rgba(255,255,255,0.7)', mt: 2, fontSize: 14 }}>
      {message}
    </Box>
  </Box>
);

/**
 * Inline loading indicator
 */
export const InlineLoader = ({ size = 24, color = 'primary' }) => (
  <Box
    sx={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <Box
      sx={{
        width: size,
        height: size,
        border: `2px solid rgba(144, 202, 249, 0.2)`,
        borderTop: `2px solid ${color === 'primary' ? '#90caf9' : color}`,
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
        '@keyframes spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      }}
    />
  </Box>
);

export default {
  ChartSkeleton,
  TableSkeleton,
  StatCardSkeleton,
  DashboardSkeleton,
  LoadingOverlay,
  InlineLoader,
};
