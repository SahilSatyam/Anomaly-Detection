import { render, screen } from '@testing-library/react';
import App from './App';

test('renders navbar title', () => {
  render(<App />);
  const linkElement = screen.getByText(/Stock Anomaly Detection/i);
  expect(linkElement).toBeInTheDocument();
});
