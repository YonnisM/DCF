# DCF Backend Utilities

This repository contains a minimal backend helper for a discounted cash flow (DCF) application. The script in `src/comprehensiveDataFetch.js` retrieves:

* Latest financial data from Yahoo Finance for a supplied ticker
* A link to the most recent annual report PDF found on the web
* AI-based analysis of the PDF to extract assumptions (requires an OpenAI API key)

## Usage

```bash
npm install
OPENAI_API_KEY=your_key npm test  # runs the fetch for AAPL by default
```

You can run the script for another ticker using:

```bash
node src/comprehensiveDataFetch.js MSFT
```

The script prints a JSON payload with quote, profile and optional `pdfAnalysis` information that can be consumed by a frontend DCF calculator.