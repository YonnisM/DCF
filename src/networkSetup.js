// File: src/networkSetup.js
// Purpose: Process-wide networking safeguards for Node + undici.

import dns from 'node:dns';
import { Agent, ProxyAgent, setGlobalDispatcher } from 'undici';

// Prefer IPv4 to avoid IPv6-only routes that trigger ENETUNREACH.
dns.setDefaultResultOrder?.('ipv4first');

const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY;

const dispatcher = proxyUrl
  ? new ProxyAgent(proxyUrl)
  : new Agent({
      // Keep it simple; shorter connect timeout reduces long hangs behind firewalls.
      connect: { timeout: 15_000 },
    });

setGlobalDispatcher(dispatcher);
