# Network Setup Notes

Run notes (add to your project README if useful):

1. Ensure Node >= 18.17 (bundled undici) or install undici explicitly.
2. If behind a proxy: export `HTTPS_PROXY=http://user:pass@host:port`.
3. Prefer IPv4 if IPv6 is flaky (Docker/WSL): handled in `networkSetup.js`.
4. Common fix in CI: run with `NODE_OPTIONS=--dns-result-order=ipv4first`.
