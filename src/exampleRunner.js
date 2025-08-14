// File: src/exampleRunner.js
// Purpose: Small runner to verify behavior locally.

import { fetchComprehensiveData } from './comprehensiveDataFetch.js';

// Edit the tickers list as needed.
const tickers = (process.env.TICKERS || 'AAPL,MSFT,TSLA').split(',');

try {
  const data = await fetchComprehensiveData({ tickers });
  console.dir(data, { depth: 2 });
} catch (err) {
  console.error('Fatal:', err);
  process.exitCode = 1;
}
