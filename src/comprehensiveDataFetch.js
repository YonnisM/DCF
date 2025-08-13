import yahooFinance from 'yahoo-finance2';
import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import pdfParse from 'pdf-parse/lib/pdf-parse.js';
import OpenAI from 'openai';

async function fetchYahooFinanceData(ticker) {
  const quote = await yahooFinance.quote(ticker);
  const summary = await yahooFinance.quoteSummary(ticker, {
    modules: ['price','summaryProfile','summaryDetail','defaultKeyStatistics','financialData','incomeStatementHistory','balanceSheetHistory','cashflowStatementHistory']
  });

  const companyName = summary.price?.longName || summary.price?.shortName || ticker;
  const income = summary.incomeStatementHistory?.incomeStatementHistory?.[0];
  const balance = summary.balanceSheetHistory?.balanceSheetStatements?.[0];
  const cashflow = summary.cashflowStatementHistory?.cashflowStatements?.[0];

  const financials = {
    revenue: income?.totalRevenue || null,
    ebitMargin: income?.ebit && income?.totalRevenue ? income.ebit / income.totalRevenue : null,
    taxRate: income?.incomeTaxExpense && income?.incomeBeforeTax ? income.incomeTaxExpense / income.incomeBeforeTax : null,
    daPct: cashflow?.depreciation && income?.totalRevenue ? cashflow.depreciation / income.totalRevenue : null,
    capexPct: cashflow?.capitalExpenditures && income?.totalRevenue ? Math.abs(cashflow.capitalExpenditures) / income.totalRevenue : null,
    nwcPct: null,
    netDebt: balance ? (balance.totalDebt || 0) - (balance.cash || 0) : null
  };

  return {
    ticker,
    currency: summary.price?.currency || 'USD',
    quote: {
      price: quote.regularMarketPrice || null,
      marketCap: quote.marketCap || null
    },
    profile: {
      companyName,
      website: summary.summaryProfile?.website || null,
      beta: summary.summaryDetail?.beta || null,
      sharesOutstanding: summary.defaultKeyStatistics?.sharesOutstanding || null
    },
    financials
  };
}

async function findAnnualReportPdf(companyName) {
  const query = encodeURIComponent(`${companyName} annual report pdf`);
  const url = `https://duckduckgo.com/html/?q=${query}`;
  const html = await fetch(url, {
    headers: {
      // DuckDuckGo may block requests without a User-Agent. Use a common browser string.
      'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    },
  }).then((r) => r.text());
  const $ = cheerio.load(html);
  let pdfUrl = null;
  $('a.result__a').each((_, el) => {
    const href = $(el).attr('href');
    if (href && href.toLowerCase().includes('.pdf')) {
      pdfUrl = href;
      return false;
    }
    return undefined;
  });
  return pdfUrl;
}

async function analyzePdfWithAI(pdfUrl) {
  const pdfBuffer = await fetch(pdfUrl).then(r => r.arrayBuffer());
  const text = await pdfParse(Buffer.from(pdfBuffer)).then(d => d.text);
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const prompt = `You are an investment analyst. Given the following annual report text, estimate a reasonable revenue CAGR, EBIT margin, and capex percentage for the next 5 years. Return a JSON object with keys revenueCagr, ebitMargin, capexPct and a short justification.\n\nText:\n${text.slice(0,12000)}`;
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.2
  });
  let structured = null;
  const content = completion.choices[0]?.message?.content || '';
  try {
    structured = JSON.parse(content);
  } catch {
    // ignore json parse errors
  }
  return { url: pdfUrl, insights: content, structured };
}

export async function fetchComprehensiveData(ticker) {
  const baseData = await fetchYahooFinanceData(ticker);
  const pdfUrl = await findAnnualReportPdf(baseData.profile.companyName || ticker);
  let pdfAnalysis = null;
  if (pdfUrl) {
    try {
      pdfAnalysis = await analyzePdfWithAI(pdfUrl);
    } catch (err) {
      pdfAnalysis = { url: pdfUrl, error: err.message };
    }
  }
  return { ...baseData, pdfFilings: pdfUrl ? [pdfUrl] : [], pdfAnalysis };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const ticker = process.argv[2];
  if (!ticker) {
    console.error('Usage: node comprehensiveDataFetch.js <TICKER>');
    process.exit(1);
  }
  fetchComprehensiveData(ticker)
    .then(res => {
      console.log(JSON.stringify(res, null, 2));
    })
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}
