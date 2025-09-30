import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Import source map blocking first (before any other imports)
import './utils/blockSourceMaps.js';
// Import development utilities for console filtering
import './utils/devtools.js';
import { suppressConsoleWarnings } from './utils/suppressConsoleWarnings.js';

// Apply console warning suppression in development
suppressConsoleWarnings();

const root = createRoot(document.getElementById('root'));
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
