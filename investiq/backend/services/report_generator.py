"""
InvestIQ Report Generator
Generates structured investment reports in HTML and plain text formats.
"""

import time
from typing import Dict, Any


def generate_html_report(analysis: Dict[str, Any]) -> str:
    """Generate a full HTML investment report."""
    company = analysis.get("company", {})
    rec = analysis.get("recommendation", {})
    kpis = analysis.get("kpis", {})
    risk = analysis.get("risk", {})
    sentiment = analysis.get("sentiment", {})
    forecast = analysis.get("forecast", {})
    comp = analysis.get("competitor_analysis", {})
    ratios = analysis.get("ratios", {})
    trace = analysis.get("agent_trace", [])
    validation = {"score": analysis.get("data_quality"), "label": analysis.get("data_quality_label")}

    def kv(key):
        return kpis.get(key, {}).get("value")

    def fmt(v, suffix="", prefix=""):
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{prefix}{v:,.2f}{suffix}"
        return f"{prefix}{v}{suffix}"

    action = rec.get("action", "N/A")
    action_color = {
        "STRONG BUY": "#16a34a",
        "BUY": "#22c55e",
        "HOLD": "#f59e0b",
        "UNDERWEIGHT": "#f97316",
        "SELL": "#ef4444",
    }.get(action, "#64748b")

    key_reasons_html = "".join(f"<li>{r}</li>" for r in rec.get("key_reasons", []))
    main_risks_html = "".join(f"<li>{r}</li>" for r in rec.get("main_risks", []))

    risk_rows = "".join(
        f"<tr><td>{r['name']}</td><td><span class='badge badge-{r['severity'].lower()}'>{r['severity']}</span></td>"
        f"<td>{r['evidence']}</td></tr>"
        for r in risk.get("risks", [])
    )

    news_rows = "".join(
        f"<tr><td>{n.get('headline','')}</td>"
        f"<td><span class='badge badge-{n.get('sentiment','neutral')}'>{n.get('sentiment','neutral').title()}</span></td>"
        f"<td>{n.get('source','')}</td><td>{n.get('published_at','')}</td></tr>"
        for n in sentiment.get("recent_headlines", [])[:6]
    )

    comp_rows = ""
    for entity in comp.get("entities", []):
        is_primary = entity.get("is_primary", False)
        row_class = "primary-row" if is_primary else ""
        comp_rows += (
            f"<tr class='{row_class}'>"
            f"<td><b>{entity.get('ticker','')}</b></td>"
            f"<td>{entity.get('name','')}</td>"
            f"<td>{fmt(entity.get('revenue_growth'), '%')}</td>"
            f"<td>{fmt(entity.get('net_margin'), '%')}</td>"
            f"<td>{fmt(entity.get('roe'), '%')}</td>"
            f"<td>{fmt(entity.get('pe'), 'x')}</td>"
            f"<td>{fmt(entity.get('debt_to_equity'), 'x')}</td>"
            f"<td>{entity.get('rank', '')}</td>"
            f"<td>{entity.get('financial_score', 'N/A')}</td>"
            f"</tr>"
        )

    trace_rows = "".join(
        (lambda s, summ: (
            f"<tr><td>{t.get('stage_name','')}</td>"
            f"<td><span class='badge badge-{s}'>{t.get('status','').title()}</span></td>"
            f"<td>{t.get('execution_time', 0):.3f}s</td>"
            f"<td>{summ[:120]}{'...' if len(summ) > 120 else ''}</td>"
            f"</tr>"
        ))(
            "completed" if t.get("status") == "completed" else "failed",
            t.get("summary", "")
        )
        for t in trace
    )

    cs = rec.get("component_scores", {})
    score_bars = "".join(
        f"""<div class='score-row'>
              <div class='score-label'>{label}</div>
              <div class='score-bar-wrap'>
                <div class='score-bar' style='width:{cs.get(key, 0):.0f}%'></div>
              </div>
              <div class='score-val'>{cs.get(key, 0):.0f}</div>
            </div>"""
        for key, label in [
            ("financial_health", "Financial Health"),
            ("growth", "Growth"),
            ("valuation", "Valuation"),
            ("competitive", "Competitive Position"),
            ("sentiment", "Market Sentiment"),
            ("risk", "Risk Profile"),
        ]
    )

    demo_banner = ""
    if analysis.get("is_demo"):
        demo_banner = "<div class='demo-banner'>⚠️ DEMO DATA — Not real-time market data</div>"

    timestamp = analysis.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    rev_growth_class = "positive" if (kv("revenue_growth") or 0) > 0 else "negative"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InvestIQ Report — {company.get('name', analysis.get('ticker', ''))} — {timestamp[:10]}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; font-size: 14px; line-height: 1.6; }}
  .page {{ max-width: 900px; margin: 0 auto; padding: 40px 24px; }}
  h1 {{ font-size: 28px; font-weight: 700; color: #0f172a; }}
  h2 {{ font-size: 18px; font-weight: 600; color: #1e40af; margin: 28px 0 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }}
  h3 {{ font-size: 15px; font-weight: 600; margin: 16px 0 8px; }}
  p {{ margin: 6px 0; color: #475569; }}
  .demo-banner {{ background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 8px 16px; border-radius: 6px; margin-bottom: 16px; font-weight: 600; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }}
  .company-name {{ font-size: 22px; font-weight: 700; }}
  .company-meta {{ color: #64748b; font-size: 13px; }}
  .rec-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin: 20px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
  .action-badge {{ font-size: 28px; font-weight: 800; color: {action_color}; letter-spacing: 2px; }}
  .rec-meta {{ display: flex; gap: 24px; flex-wrap: wrap; }}
  .rec-meta-item {{ text-align: center; }}
  .rec-meta-item .val {{ font-size: 20px; font-weight: 700; }}
  .rec-meta-item .lbl {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin: 12px 0; }}
  .kpi-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; }}
  .kpi-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }}
  .kpi-value {{ font-size: 18px; font-weight: 700; }}
  .kpi-change {{ font-size: 12px; margin-top: 2px; }}
  .positive {{ color: #16a34a; }} .negative {{ color: #dc2626; }} .stable {{ color: #94a3b8; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
  th {{ background: #f1f5f9; padding: 8px 12px; text-align: left; font-weight: 600; color: #475569; }}
  td {{ padding: 8px 12px; border-top: 1px solid #e2e8f0; }}
  tr.primary-row {{ background: #eff6ff; font-weight: 600; }}
  .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
  .badge-completed {{ background: #dcfce7; color: #16a34a; }}
  .badge-positive {{ background: #dcfce7; color: #16a34a; }}
  .badge-neutral {{ background: #f1f5f9; color: #64748b; }}
  .badge-negative {{ background: #fee2e2; color: #dc2626; }}
  .badge-high {{ background: #fee2e2; color: #dc2626; }}
  .badge-moderate {{ background: #fef3c7; color: #d97706; }}
  .badge-low {{ background: #dcfce7; color: #16a34a; }}
  .badge-critical {{ background: #7f1d1d; color: #fff; }}
  .score-row {{ display: flex; align-items: center; gap: 10px; margin: 6px 0; }}
  .score-label {{ width: 160px; font-size: 13px; color: #475569; }}
  .score-bar-wrap {{ flex: 1; background: #e2e8f0; border-radius: 4px; height: 10px; overflow: hidden; }}
  .score-bar {{ height: 100%; background: #3b82f6; border-radius: 4px; }}
  .score-val {{ width: 36px; font-weight: 700; font-size: 13px; text-align: right; }}
  .disclaimer {{ background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 14px 18px; margin: 28px 0; font-size: 12px; color: #78350f; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 11px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; }}
  @media print {{ body {{ background: white; }} .page {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="page">
  {demo_banner}
  <div class="header">
    <div>
      <div style="font-size:12px;color:#3b82f6;font-weight:700;letter-spacing:2px;margin-bottom:4px;">INVESTIQ — SEQUENTIAL AI INVESTMENT ANALYST</div>
      <h1>{company.get('name', analysis.get('ticker', ''))} ({analysis.get('ticker', '')})</h1>
      <div class="company-meta">{company.get('sector','N/A')} · {company.get('industry','N/A')} · {company.get('exchange','N/A')}</div>
    </div>
    <div style="text-align:right;font-size:12px;color:#94a3b8;">
      Report generated: {timestamp[:16].replace('T',' ')} UTC<br>
      Data quality: <b>{validation.get('score','N/A')}/100</b> ({validation.get('label','N/A')})<br>
      Analysis ID: {analysis.get('id','N/A')[:12]}...
    </div>
  </div>

  <h2>Investment Recommendation</h2>
  <div class="rec-card">
    <div class="action-badge">{action}</div>
    <div class="rec-meta">
      <div class="rec-meta-item">
        <div class="val">{rec.get('score','N/A')}<span style="font-size:14px;">/100</span></div>
        <div class="lbl">Investment Score</div>
      </div>
      <div class="rec-meta-item">
        <div class="val">{rec.get('confidence','N/A')}%</div>
        <div class="lbl">Confidence</div>
      </div>
      <div class="rec-meta-item">
        <div class="val">{risk.get('level','N/A')}</div>
        <div class="lbl">Risk Level</div>
      </div>
      <div class="rec-meta-item">
        <div class="val">{forecast.get('outlook','N/A')}</div>
        <div class="lbl">Outlook</div>
      </div>
    </div>
  </div>

  <h3>Key Reasons</h3>
  <ul style="margin:8px 0 16px 20px;color:#475569;">{key_reasons_html}</ul>

  <h3>Primary Risks</h3>
  <ul style="margin:8px 0 16px 20px;color:#475569;">{main_risks_html}</ul>

  <h2>Score Breakdown</h2>
  {score_bars}

  <h2>Key Financial KPIs</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-label">Revenue</div><div class="kpi-value">${fmt(kv('revenue'))}M</div></div>
    <div class="kpi-card"><div class="kpi-label">Revenue Growth</div><div class="kpi-value {rev_growth_class}">{fmt(kv('revenue_growth'), '%')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Net Margin</div><div class="kpi-value">{fmt(kv('net_margin'), '%')}</div></div>
    <div class="kpi-card"><div class="kpi-label">EPS</div><div class="kpi-value">${fmt(kv('eps'))}</div></div>
    <div class="kpi-card"><div class="kpi-label">ROE</div><div class="kpi-value">{fmt(kv('roe'), '%')}</div></div>
    <div class="kpi-card"><div class="kpi-label">P/E Ratio</div><div class="kpi-value">{fmt(kv('pe'), 'x')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Debt/Equity</div><div class="kpi-value">{fmt(kv('debt_to_equity'), 'x')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Free Cash Flow</div><div class="kpi-value">${fmt(kv('free_cash_flow'))}M</div></div>
    <div class="kpi-card"><div class="kpi-label">EBITDA</div><div class="kpi-value">${fmt(kv('ebitda'))}M</div></div>
    <div class="kpi-card"><div class="kpi-label">Gross Margin</div><div class="kpi-value">{fmt(kv('gross_margin'), '%')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Operating Margin</div><div class="kpi-value">{fmt(kv('operating_margin'), '%')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Current Ratio</div><div class="kpi-value">{fmt(kv('current_ratio'), 'x')}</div></div>
  </div>

  <h2>Competitor Benchmarking</h2>
  <table>
    <tr><th>Ticker</th><th>Name</th><th>Rev Growth</th><th>Net Margin</th><th>ROE</th><th>P/E</th><th>D/E</th><th>Rank</th><th>Score</th></tr>
    {comp_rows}
  </table>

  <h2>Market Sentiment</h2>
  <p>Sentiment Score: <b>{sentiment.get('score', 'N/A')}</b> ({sentiment.get('label','N/A')}) &nbsp;|&nbsp;
     Positive: {sentiment.get('positive_pct',0):.0f}% &nbsp;|&nbsp;
     Neutral: {sentiment.get('neutral_pct',0):.0f}% &nbsp;|&nbsp;
     Negative: {sentiment.get('negative_pct',0):.0f}%
  </p>
  <table>
    <tr><th>Headline</th><th>Sentiment</th><th>Source</th><th>Date</th></tr>
    {news_rows}
  </table>

  <h2>Risk Assessment</h2>
  <p>Overall Risk: <b>{risk.get('score','N/A')}/100</b> — {risk.get('level','N/A')}</p>
  <table>
    <tr><th>Risk Factor</th><th>Severity</th><th>Evidence</th></tr>
    {risk_rows}
  </table>

  <h2>Trend & Forecast</h2>
  <p><b>Outlook:</b> {forecast.get('outlook','N/A')} &nbsp;|&nbsp; <b>Confidence:</b> {forecast.get('confidence','N/A')}%</p>
  <p>{forecast.get('outlook_note','')}</p>
  <h3>Bullish Factors</h3>
  <ul style="margin:8px 0 12px 20px;color:#16a34a;">{''.join(f'<li>{f}</li>' for f in forecast.get('bullish_factors',[]))}</ul>
  <h3>Bearish Factors</h3>
  <ul style="margin:8px 0 12px 20px;color:#dc2626;">{''.join(f'<li>{f}</li>' for f in forecast.get('bearish_factors',[]))}</ul>

  <h2>Agent Execution Trace</h2>
  <table>
    <tr><th>Stage</th><th>Status</th><th>Time</th><th>Summary</th></tr>
    {trace_rows}
  </table>

  <div class="disclaimer">
    ⚠️ <b>Responsible Investment Disclaimer:</b> {rec.get('disclaimer', 'This report is for educational and informational purposes only. Not financial advice.')}
  </div>

  <div class="footer">
    Generated by InvestIQ Sequential AI Investment Analyst · {timestamp[:10]} ·
    Data: {'Demo Mode' if analysis.get('is_demo') else 'Live API'} ·
    Total execution time: {analysis.get('total_execution_time', 0):.2f}s
  </div>
</div>
</body>
</html>"""

    return html
