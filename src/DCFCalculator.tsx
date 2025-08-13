import React, { useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, BarChart, Bar } from "recharts";
import { RefreshCw, Download, SlidersHorizontal, Building2, FileText, AlertTriangle, Brain, TrendingUp } from "lucide-react";
import { computeDcf, DcfInputs, DcfAssumptions } from "@/lib/dcf";
import { fetchYahooFinanceData } from "@/services/yahooFinance";
import { analyzeCompanyWithAI } from "@/services/openaiAnalysis";
import { toast } from "sonner";

const fmtCurr = (n: number | null, c = "USD", d = 0) =>
  n == null || isNaN(n)
    ? "–"
    : new Intl.NumberFormat(undefined, { style: "currency", currency: c, maximumFractionDigits: d }).format(n);
const pct = (x: number | null, d = 1) => (x == null ? "–" : `${(x * 100).toFixed(d)}%`);
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const toNum = (v: string | number, f = 0) => {
  const n = typeof v === "string" ? parseFloat(v.replace(/[, %]/g, "")) : Number(v);
  return Number.isFinite(n) ? n : f;
};

const demo = {
  ticker: "AAPL",
  currency: "USD",
  quote: { price: 230, marketCap: 3.5e12 },
  profile: {
    companyName: "Apple Inc.",
    sharesOutstanding: 15.5e9,
    beta: 1.2,
  },
  financials: {
    revenue: 385e9,
    ebitMargin: 0.3,
    taxRate: 0.16,
    daPct: 0.03,
    capexPct: 0.03,
    nwcPct: 0.0,
    netDebt: -6e10,
  },
};

interface PctProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}
const Pct = ({ label, value, onChange, min = 0, max = 1, step = 0.005 }: PctProps) => (
  <div className="space-y-1">
    <div className="flex justify-between text-sm"><Label>{label}</Label><span className="font-mono">{pct(value)}</span></div>
    <Slider value={[clamp(value, min, max)]} min={min} max={max} step={step} onValueChange={v => onChange(clamp(v[0], min, max))} />
  </div>
);

interface NumProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: number;
  min?: number;
  max?: number;
  suffix?: string;
}
const Num = ({ label, value, onChange, step = 1, min, max, suffix }: NumProps) => (
  <div className="flex items-center justify-between gap-2 py-1">
    <Label className="text-sm">{label}</Label>
    <div className="flex items-center gap-2">
      <Input type="number" value={value} onChange={e => onChange(toNum(e.target.value, value))} step={step} min={min} max={max} className="w-28 h-9" />
      {suffix ? <span className="text-xs text-muted-foreground">{suffix}</span> : null}
    </div>
  </div>
);

export default function DCFCalculator() {
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState(demo);
  const [years, setYears] = useState(5);
  const ccy = data.currency;
  const price = data.quote.price;
  const startRev = data.financials.revenue;
  const sharesDefault = data.profile.sharesOutstanding;
  const netDebtDefault = data.financials.netDebt;

  const [scenarios, setScenarios] = useState({
    base: {
      revenueGrowth: 0.05,
      ebitMargin: data.financials.ebitMargin,
      taxRate: data.financials.taxRate,
      daPct: data.financials.daPct,
      capexPct: data.financials.capexPct,
      nwcPct: data.financials.nwcPct,
      wacc: 0.1,
      terminalGrowth: 0.025,
      shares: sharesDefault,
      netDebt: netDebtDefault,
      prob: 6,
    },
  });

  useEffect(() => {
    setScenarios(prev => ({
      base: { ...prev.base, shares: sharesDefault, netDebt: netDebtDefault },
    }));
  }, [sharesDefault, netDebtDefault]);

  const dcfResults = useMemo(() => {
    const scenario = scenarios.base;
    const inputs: DcfInputs = {
      revenue0: startRev,
      ebitMargin0Pct: scenario.ebitMargin * 100,
      netDebt: scenario.netDebt,
      sharesOutstanding: scenario.shares,
      lastPrice: price,
      currency: ccy,
    };
    const assumptions: DcfAssumptions = {
      years,
      revCagrPct: scenario.revenueGrowth * 100,
      termEbitMarginPct: scenario.ebitMargin * 100,
      daPctSales: scenario.daPct * 100,
      capexPctSales: scenario.capexPct * 100,
      deltaNwcPctDeltaSales: scenario.nwcPct * 100,
      taxRatePct: scenario.taxRate * 100,
      waccPct: scenario.wacc * 100,
      terminal: { method: "gordon", gPct: scenario.terminalGrowth * 100 },
    };
    try {
      return computeDcf(inputs, assumptions, { includeSensitivity: true });
    } catch (err) {
      console.error("DCF calculation error", err);
      return null;
    }
  }, [scenarios, startRev, years, price, ccy]);

  async function fetchYahoo() {
    try {
      setData(await fetchYahooFinanceData(ticker) as any);
      toast.success(`Loaded ${ticker} data`);
    } catch (e: any) {
      toast.error("Failed to load: " + e.message);
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Company Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex gap-2">
            <Input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} />
            <Button onClick={fetchYahoo} disabled={false}><RefreshCw className="w-4 h-4 mr-1" />Fetch</Button>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div>Price: {fmtCurr(price, ccy)}</div>
            <div>Market Cap: {fmtCurr(data.quote.marketCap, ccy)}</div>
            <div>Beta: {data.profile.beta}</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Base Case Assumptions</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <Pct label="Revenue CAGR" value={scenarios.base.revenueGrowth} onChange={v => setScenarios({ base: { ...scenarios.base, revenueGrowth: v } })} min={-0.2} max={0.3} />
          <Pct label="EBIT Margin" value={scenarios.base.ebitMargin} onChange={v => setScenarios({ base: { ...scenarios.base, ebitMargin: v } })} min={0} max={0.5} />
          <Pct label="D&A (% Sales)" value={scenarios.base.daPct} onChange={v => setScenarios({ base: { ...scenarios.base, daPct: v } })} min={0} max={0.1} />
          <Pct label="Capex (% Sales)" value={scenarios.base.capexPct} onChange={v => setScenarios({ base: { ...scenarios.base, capexPct: v } })} min={0} max={0.2} />
          <Pct label="ΔNWC (% ΔSales)" value={scenarios.base.nwcPct} onChange={v => setScenarios({ base: { ...scenarios.base, nwcPct: v } })} min={-0.1} max={0.1} />
          <Pct label="WACC" value={scenarios.base.wacc} onChange={v => setScenarios({ base: { ...scenarios.base, wacc: v } })} min={0.04} max={0.2} />
          <Pct label="Terminal g" value={scenarios.base.terminalGrowth} onChange={v => setScenarios({ base: { ...scenarios.base, terminalGrowth: v } })} min={0} max={0.05} />
          <Num label="Forecast Years" value={years} onChange={setYears} step={1} min={3} max={15} />
        </CardContent>
      </Card>

      {dcfResults && (
        <Card>
          <CardHeader>
            <CardTitle>DCF Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>Enterprise Value: {fmtCurr(dcfResults.ev, ccy)}</div>
            <div>Equity Value: {fmtCurr(dcfResults.eq, ccy)}</div>
            <div>Intrinsic Value / Share: {fmtCurr(dcfResults.perShare, ccy)}</div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
