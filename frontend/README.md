# Stock Anomaly Detection - Frontend

A modern React application for visualizing stock data and detecting anomalies in stock price movements, specifically focused on the "Magnificent 7" tech stocks.

## Features

- Real-time stock price visualization using candlestick charts
- Volume analysis with color-coded histogram
- Anomaly detection visualization
- Modern, responsive UI with Material-UI components
- Dark theme optimized for financial data viewing
- Interactive chart controls (zoom, pan, time range selection)
- Stock selection for Magnificent 7 companies (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)

## Prerequisites

- Node.js (v14.0.0 or higher)
- npm (v6.0.0 or higher)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock_anomaly_detection.git
cd stock_anomaly_detection/frontend
```

2. Install dependencies:
```bash
npm install
```

## Development

To start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`

## Building for Production

To create a production build:

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable React components
│   │   ├── Charts.jsx     # Stock chart visualization
│   │   ├── AnomalyList.jsx# Anomaly detection display
│   │   └── StockSelector.jsx# Stock selection component
│   ├── pages/             # Page components
│   │   └── Dashboard.jsx  # Main dashboard page
│   ├── App.js            # Root component
│   └── index.js          # Entry point
├── public/               # Static assets
└── package.json         # Project dependencies and scripts
```

## Key Dependencies

- React (^18.0.0)
- Material-UI (@mui/material)
- Lightweight Charts (^5.0.5)
- Other utilities and development tools

## Features in Detail

### Stock Chart Component
- Candlestick chart for price visualization
- Volume histogram with color-coded bars
- Interactive crosshair and tooltips
- Responsive design with automatic resizing
- Time range selection and navigation

### Anomaly Detection
- Visual indicators for detected anomalies
- Detailed anomaly information display
- Filtering and sorting capabilities
- Real-time updates

### Stock Selection
- Focused on Magnificent 7 tech stocks
- Easy-to-use dropdown interface
- Real-time data updates
- Persistent selection state

## Configuration

The application can be configured through environment variables:

```env
REACT_APP_API_URL=http://localhost:8000  # Backend API URL
```

## Browser Support

The application is tested and supported on:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
