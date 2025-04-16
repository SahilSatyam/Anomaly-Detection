import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

// Magnificent 7 companies
const MAGNIFICENT_7 = [
  { symbol: "AAPL", name: "Apple Inc." },
  { symbol: "MSFT", name: "Microsoft Corporation" },
  { symbol: "GOOGL", name: "Alphabet Inc." },
  { symbol: "AMZN", name: "Amazon.com Inc." },
  { symbol: "NVDA", name: "NVIDIA Corporation" },
  { symbol: "META", name: "Meta Platforms Inc." },
  { symbol: "TSLA", name: "Tesla Inc." }
];

const StockSelector = ({ value, onChange, disabled = false }) => {
  return (
    <FormControl fullWidth>
      <InputLabel>Stock</InputLabel>
      <Select
        value={value}
        label="Stock"
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {MAGNIFICENT_7.map((stock) => (
          <MenuItem key={stock.symbol} value={stock.symbol}>
            {stock.symbol} - {stock.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default StockSelector; 