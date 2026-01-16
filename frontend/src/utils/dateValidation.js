/**
 * Date Validation Utilities
 * 
 * Provides validation functions for date inputs.
 */

/**
 * Validate that start date is before or equal to end date
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @returns {Object} Validation result with isValid and error message
 */
export const validateDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) {
    return { isValid: false, error: 'Both start and end dates are required' };
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (isNaN(start.getTime())) {
    return { isValid: false, error: 'Invalid start date format' };
  }

  if (isNaN(end.getTime())) {
    return { isValid: false, error: 'Invalid end date format' };
  }

  if (start > end) {
    return { isValid: false, error: 'Start date must be before or equal to end date' };
  }

  // Check if date range is too large (e.g., more than 5 years)
  const maxDays = 365 * 5;
  const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
  if (diffDays > maxDays) {
    return { 
      isValid: false, 
      error: `Date range cannot exceed ${maxDays} days (approximately 5 years)` 
    };
  }

  // Check if end date is in the future (more than today)
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  if (end > today) {
    return { isValid: false, error: 'End date cannot be in the future' };
  }

  return { isValid: true, error: null };
};

/**
 * Get date range presets
 * @returns {Array} Array of preset options
 */
export const getDatePresets = () => {
  const today = new Date();
  
  return [
    {
      label: 'Last 7 days',
      value: '7d',
      getRange: () => ({
        start: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000),
        end: today
      })
    },
    {
      label: 'Last 30 days',
      value: '30d',
      getRange: () => ({
        start: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000),
        end: today
      })
    },
    {
      label: 'Last 90 days',
      value: '90d',
      getRange: () => ({
        start: new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000),
        end: today
      })
    },
    {
      label: 'Last 6 months',
      value: '6m',
      getRange: () => ({
        start: new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000),
        end: today
      })
    },
    {
      label: 'Last year',
      value: '1y',
      getRange: () => ({
        start: new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000),
        end: today
      })
    },
    {
      label: 'Year to date',
      value: 'ytd',
      getRange: () => ({
        start: new Date(today.getFullYear(), 0, 1),
        end: today
      })
    }
  ];
};

/**
 * Format date for display
 * @param {Date|string} date - Date to format
 * @param {string} format - Format type: 'short', 'long', 'iso'
 * @returns {string} Formatted date string
 */
export const formatDate = (date, format = 'short') => {
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid date';

  switch (format) {
    case 'long':
      return d.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    case 'iso':
      return d.toISOString().split('T')[0];
    case 'short':
    default:
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
  }
};

/**
 * Parse date from various formats
 * @param {string|Date} dateInput - Date input
 * @returns {Date|null} Parsed Date object or null if invalid
 */
export const parseDate = (dateInput) => {
  if (!dateInput) return null;
  
  if (dateInput instanceof Date) {
    return isNaN(dateInput.getTime()) ? null : dateInput;
  }

  const parsed = new Date(dateInput);
  return isNaN(parsed.getTime()) ? null : parsed;
};
