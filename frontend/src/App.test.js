import { render, screen } from '@testing-library/react';
import App from './App';

test('renders InnovateSphere header', () => {
  render(<App />);
  const headerElement = screen.getByText('InnovateSphere');
  expect(headerElement).toBeInTheDocument();
});
