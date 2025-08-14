// File: src/utils/netRetry.js
// Purpose: Small retry helper focused on transient network failures.

import { setTimeout as delay } from 'node:timers/promises';

/**
 * Classifies errors that are likely transient network issues.
 */
export function isTransientNetworkError(err) {
  const code = err?.code || err?.cause?.code;
  if (!code && err?.name === 'TypeError' && /fetch failed/i.test(err?.message || '')) return true;
  const retriableCodes = new Set([
    'ENETUNREACH',
    'ECONNRESET',
    'ECONNREFUSED',
    'EAI_AGAIN',
    'ETIMEDOUT',
    'UND_ERR_SOCKET',
    'UND_ERR_CONNECT_TIMEOUT',
    'UND_ERR_HEADERS_TIMEOUT',
    'UND_ERR_BODY_TIMEOUT',
  ]);
  return retriableCodes.has(code);
}

/**
 * Retry wrapper with exponential backoff.
 */
export async function withRetry(task, {
  retries = 3,
  baseDelayMs = 600,
  maxDelayMs = 5_000,
  onRetry = () => {},
} = {}) {
  let attempt = 0;
  let lastErr;
  while (attempt <= retries) {
    try {
      return await task();
    } catch (err) {
      lastErr = err;
      if (attempt === retries || !isTransientNetworkError(err)) break;
      const delayMs = Math.min(baseDelayMs * 2 ** attempt, maxDelayMs);
      await onRetry(err, attempt + 1, delayMs);
      await delay(delayMs);
      attempt += 1;
    }
  }
  throw lastErr;
}

export function normalizeNetworkError(err) {
  const code = err?.code || err?.cause?.code;
  const message = err?.message || 'Unknown network error';
  return {
    name: err?.name || 'Error',
    code,
    message,
    cause: err?.cause?.message || undefined,
    hints: buildHints(code, message),
  };
}

function buildHints(code, message) {
  const hints = [];
  if (code === 'ENETUNREACH') {
    hints.push('No internet route from container/host. Check VPN, firewall, or Docker network.');
    hints.push('If your network is IPv6-problematic, prefer IPv4: dns.setDefaultResultOrder("ipv4first").');
  }
  if (/fetch failed/i.test(message)) {
    hints.push('Ensure outbound HTTPS to *.yahoo.com is allowed.');
  }
  if (process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY) {
    hints.push('Proxy detected via env; verify it is reachable and whitelisted.');
  } else {
    hints.push('If behind a corporate proxy, set HTTPS_PROXY / HTTP_PROXY.');
  }
  hints.push('Retry is enabled; transient outages usually recover.');
  return hints;
}
