# Stock Anomaly Detection - Frontend

Modern React application for visualizing stock data and anomalies with real-time updates and export capabilities.

## ✨ Features

- **Interactive Charts**: Candlestick charts with volume overlay using Lightweight Charts
- **Anomaly Visualization**: Markers on charts showing detected anomalies by severity
- **Real-time Updates**: Auto-refresh with configurable polling interval
- **Data Export**: Download data as CSV or generate PDF reports
- **Dark Theme**: Modern UI optimized for financial data viewing
- **Responsive Design**: Works on desktop and tablet devices

## 📋 Prerequisites

- Node.js 18+ (20 recommended)
- npm 8+

## 🚀 Quick Start

### Installation

```bash
npm install
```

### Development

```bash
npm start
```

Application runs at http://localhost:3000

### Production Build

```bash
npm run build
```

Build output in `build/` directory.

## ⚙️ Configuration

Create `.env.local` for local settings:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
REACT_APP_REFRESH_INTERVAL=60000
```

| Variable                     | Description                | Default                 |
| ---------------------------- | -------------------------- | ----------------------- |
| `REACT_APP_API_URL`          | Backend API URL            | `http://localhost:8000` |
| `REACT_APP_DEBUG`            | Enable debug mode          | `false`                 |
| `REACT_APP_REFRESH_INTERVAL` | Auto-refresh interval (ms) | `60000`                 |

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Charts.jsx            # Candlestick chart with anomaly markers
│   │   ├── Anomalies.jsx         # Anomaly list table
│   │   ├── HistoricalRecords.jsx # Stock price history
│   │   ├── StockSelector.jsx     # Stock dropdown
│   │   ├── LoadingSkeleton.jsx   # Shimmer loading states
│   │   └── ExportToolbar.jsx     # CSV/PDF export
│   │
│   ├── pages/             # Page components
│   │   ├── Dashboard.jsx  # Main dashboard
│   │   └── Settings.jsx   # Settings page
│   │
│   ├── hooks/             # Custom React hooks
│   │   └── useDataFetching.js    # Data fetching with polling
│   │
│   ├── utils/             # Utility functions
│   │   ├── dateValidation.js     # Date range validation
│   │   └── exportData.js         # CSV/PDF export
│   │
│   ├── config/            # Configuration
│   │   └── api.js         # API endpoints & fetch wrapper
│   │
│   ├── App.js             # Root component with routing
│   └── index.js           # Entry point
│
├── nginx.conf             # Production Nginx config
├── Dockerfile             # Container image
└── package.json           # Dependencies
```

## 🧩 Key Components

### Charts

Interactive candlestick chart with:

- OHLC price data
- Volume histogram
- Anomaly markers (color-coded by severity)
- Zoom/pan controls
- Responsive sizing

### Dashboard

Main view featuring:

- Stock selector dropdown
- Date range picker with presets
- Date validation (start ≤ end)
- Auto-refresh toggle
- Export toolbar
- Collapsible historical data

### Loading States

Shimmer skeleton components:

- `ChartSkeleton` - Chart placeholder
- `TableSkeleton` - Table rows placeholder
- `DashboardSkeleton` - Full page loading

## 🔧 Custom Hooks

### `useStockData`

Fetches stock data with optional auto-refresh:

```jsx
const { stockData, anomalies, loading, error, lastUpdated, refetch } =
  useStockData("AAPL", startDate, endDate, {
    autoRefresh: true,
    refreshInterval: 60000,
  });
```

### `useHealthCheck`

Monitors API health:

```jsx
const { isHealthy, health } = useHealthCheck(30000);
```

### `useLocalStorage`

Persists state to localStorage:

```jsx
const [preferences, setPreferences] = useLocalStorage("prefs", {});
```

## 📤 Export Features

### CSV Export

- Stock price data with all OHLCV fields
- Anomalies with detection method and score

### PDF Report

- Print-friendly format
- Summary statistics
- Anomaly table

```jsx
import { exportStockDataCSV, generatePDFReport } from "./utils/exportData";

// Export prices
exportStockDataCSV(stockData, "AAPL");

// Generate report
generatePDFReport({
  stockData,
  anomalies,
  symbol: "AAPL",
  dateRange: { start: "2024-01-01", end: "2024-01-31" },
});
```

## 🧪 Testing

```bash
# Run tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watchAll
```

### Test Files

- `*.test.js` - Unit tests
- Uses Jest + React Testing Library

## 🐳 Docker

### Build Image

```bash
docker build -t anomaly-frontend .

# With custom API URL
docker build \
  --build-arg REACT_APP_API_URL=https://api.example.com \
  -t anomaly-frontend .
```

### Run Container

```bash
docker run -p 3000:80 anomaly-frontend
```

## 🎨 Theme

Material UI dark theme with custom colors:

```javascript
{
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#f48fb1' },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
}
```

## 📱 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 🔗 API Integration

API calls use centralized config from `config/api.js`:

```javascript
import { API_ENDPOINTS, apiFetch } from "./config/api";

// Fetch with error handling
const data = await apiFetch(API_ENDPOINTS.stockData);
```

Available endpoints:

- `API_ENDPOINTS.stocks` - Stock list
- `API_ENDPOINTS.stockData` - Price history
- `API_ENDPOINTS.anomalies` - Detected anomalies
- `API_ENDPOINTS.detectAnomalies` - Trigger detection
- `API_ENDPOINTS.health` - Health check

## 📝 License

MIT License - see [LICENSE](../LICENSE)
