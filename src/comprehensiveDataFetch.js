// File: src/comprehensiveDataFetch.js
// Purpose: Robust Yahoo Finance fetch with retries and actionable errors.

import './networkSetup.js';
import yahooFinance from 'yahoo-finance2';
import { withRetry, normalizeNetworkError } from './utils/netRetry.js';

/**
 * Fetch a single quote with retries.
 * @param {string} symbol - Ticker, e.g., "AAPL".
 */
export async function fetchYahooFinanceData(symbol) {
  return withRetry(
    async () => {
      // Keep query options minimal; add more if needed by your app.
      return await yahooFinance.quote(symbol);
    },
    {
      retries: 4,
      baseDelayMs: 700,
      onRetry: (err, attempt, waitMs) => {
        // Minimal log to aid debugging without flooding output.
        console.warn(
          `[yahoo-finance2] transient error (attempt ${attempt}): ${err?.code || err?.message}. Retrying in ${waitMs}ms...`
        );
      },
    }
  );
}

/**
 * Fetch multiple tickers and collect results and errors per symbol.
 * @param {{ tickers: string[] }} params
 */
export async function fetchComprehensiveData({ tickers }) {
  const results = {};
  for (const t of tickers) {
    try {
      results[t] = await fetchYahooFinanceData(t);
    } catch (err) {
      results[t] = { error: normalizeNetworkError(err) };
    }
  }
  return results;
}
