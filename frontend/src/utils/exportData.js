/**
 * Data Export Utilities
 * 
 * Functions for exporting data to CSV and PDF formats.
 */

/**
 * Convert data array to CSV string
 * @param {Array} data - Array of objects to convert
 * @param {Object} options - Export options
 * @returns {string} CSV formatted string
 */
export const convertToCSV = (data, options = {}) => {
  if (!data || !data.length) {
    return '';
  }

  const {
    columns = null, // Specific columns to include (null = all)
    headers = null, // Custom headers mapping { fieldName: 'Display Name' }
    dateFields = ['date'], // Fields to format as dates
    numberFields = [], // Fields to format as numbers
  } = options;

  // Determine columns to use
  const fields = columns || Object.keys(data[0]);
  
  // Create header row
  const headerRow = fields.map(field => {
    const header = headers?.[field] || field;
    // Escape quotes and wrap in quotes if contains comma
    return `"${String(header).replace(/"/g, '""')}"`;
  }).join(',');

  // Create data rows
  const dataRows = data.map(row => {
    return fields.map(field => {
      let value = row[field];
      
      // Handle null/undefined
      if (value === null || value === undefined) {
        return '';
      }
      
      // Format dates
      if (dateFields.includes(field) && value) {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          value = date.toISOString().split('T')[0];
        }
      }
      
      // Format numbers
      if (numberFields.includes(field) && typeof value === 'number') {
        value = value.toFixed(2);
      }
      
      // Escape and wrap strings
      return `"${String(value).replace(/"/g, '""')}"`;
    }).join(',');
  }).join('\n');

  return `${headerRow}\n${dataRows}`;
};

/**
 * Download data as CSV file
 * @param {Array} data - Data to export
 * @param {string} filename - Output filename (without extension)
 * @param {Object} options - CSV conversion options
 */
export const downloadCSV = (data, filename = 'export', options = {}) => {
  const csv = convertToCSV(data, options);
  
  if (!csv) {
    console.warn('No data to export');
    return false;
  }

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.csv`;
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
  return true;
};

/**
 * Export stock data to CSV
 * @param {Array} stockData - Stock price data
 * @param {string} symbol - Stock symbol
 */
export const exportStockDataCSV = (stockData, symbol = 'stock') => {
  return downloadCSV(stockData, `${symbol}_prices_${getDateSuffix()}`, {
    columns: ['date', 'open', 'high', 'low', 'close', 'volume'],
    headers: {
      date: 'Date',
      open: 'Open',
      high: 'High',
      low: 'Low',
      close: 'Close',
      volume: 'Volume'
    },
    dateFields: ['date'],
    numberFields: ['open', 'high', 'low', 'close']
  });
};

/**
 * Export anomalies to CSV
 * @param {Array} anomalies - Anomaly data
 * @param {string} symbol - Stock symbol
 */
export const exportAnomaliesCSV = (anomalies, symbol = 'stock') => {
  return downloadCSV(anomalies, `${symbol}_anomalies_${getDateSuffix()}`, {
    columns: ['date', 'type', 'detection_method', 'score', 'threshold', 'is_verified', 'notes'],
    headers: {
      date: 'Date',
      type: 'Type',
      detection_method: 'Detection Method',
      score: 'Score',
      threshold: 'Threshold',
      is_verified: 'Verified',
      notes: 'Notes'
    },
    dateFields: ['date'],
    numberFields: ['score', 'threshold']
  });
};

/**
 * Generate PDF report (simple HTML-based)
 * Note: For production, consider using libraries like jsPDF or pdfmake
 * @param {Object} data - Report data
 * @param {string} title - Report title
 */
export const generatePDFReport = (data, title = 'Stock Analysis Report') => {
  const { stockData = [], anomalies = [], symbol = '', dateRange = {} } = data;

  // Create HTML content for the report
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${title}</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          padding: 40px;
          max-width: 800px;
          margin: 0 auto;
          color: #333;
        }
        h1 { color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; font-weight: 600; }
        tr:nth-child(even) { background: #fafafa; }
        .summary { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .anomaly-high { background: #ffebee; }
        .anomaly-medium { background: #fff3e0; }
        .footer { margin-top: 40px; font-size: 12px; color: #999; }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      <div class="summary">
        <strong>Symbol:</strong> ${symbol}<br>
        <strong>Period:</strong> ${dateRange.start || 'N/A'} to ${dateRange.end || 'N/A'}<br>
        <strong>Generated:</strong> ${new Date().toLocaleString()}
      </div>

      <h2>Summary Statistics</h2>
      <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Data Points</td><td>${stockData.length}</td></tr>
        <tr><td>Anomalies Detected</td><td>${anomalies.length}</td></tr>
        ${stockData.length > 0 ? `
          <tr><td>Latest Close</td><td>$${stockData[stockData.length - 1]?.close?.toFixed(2) || 'N/A'}</td></tr>
          <tr><td>Average Volume</td><td>${(stockData.reduce((a, b) => a + (b.volume || 0), 0) / stockData.length).toLocaleString()}</td></tr>
        ` : ''}
      </table>

      ${anomalies.length > 0 ? `
        <h2>Detected Anomalies</h2>
        <table>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Score</th>
            <th>Method</th>
          </tr>
          ${anomalies.slice(0, 20).map(a => `
            <tr class="${a.score > 3 ? 'anomaly-high' : a.score > 2 ? 'anomaly-medium' : ''}">
              <td>${new Date(a.date).toLocaleDateString()}</td>
              <td>${a.type || 'Unknown'}</td>
              <td>${a.score?.toFixed(2) || 'N/A'}</td>
              <td>${a.detection_method || 'N/A'}</td>
            </tr>
          `).join('')}
        </table>
        ${anomalies.length > 20 ? `<p><em>Showing first 20 of ${anomalies.length} anomalies</em></p>` : ''}
      ` : '<p>No anomalies detected in this period.</p>'}

      <div class="footer">
        Generated by Stock Anomaly Detection System
      </div>
    </body>
    </html>
  `;

  // Open print dialog
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.print();
  }
};

/**
 * Get date suffix for filenames
 * @returns {string} Date suffix in YYYYMMDD format
 */
const getDateSuffix = () => {
  const now = new Date();
  return now.toISOString().split('T')[0].replace(/-/g, '');
};

/**
 * Export combined report
 * @param {Object} data - All data to export
 * @param {string} format - 'csv' or 'pdf'
 */
export const exportReport = (data, format = 'csv') => {
  const { stockData, anomalies, symbol } = data;
  
  if (format === 'pdf') {
    generatePDFReport(data, `Stock Analysis Report - ${symbol}`);
    return true;
  }
  
  // For CSV, export both files
  if (stockData?.length) {
    exportStockDataCSV(stockData, symbol);
  }
  if (anomalies?.length) {
    exportAnomaliesCSV(anomalies, symbol);
  }
  
  return true;
};
