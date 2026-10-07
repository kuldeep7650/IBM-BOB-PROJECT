/**
 * InvestIQ — Main Application JavaScript
 * Handles the full frontend workflow:
 *   Search → Pipeline progress → Results dashboard → Charts → Report
 */

"use strict";

// ═══════════════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════════════
const State = {
  analysisId: null,
  analysis: null,
  pollTimer: null,
  currentTab: "overview",
  charts: {},
};

// ═══════════════════════════════════════════════════════════════════
// API helpers
// ═══════════════════════════════════════════════════════════════════
const API = {
  async post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  },
  async get(url) {
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  },
};

// ═══════════════════════════════════════════════════════════════════
// Toast notifications
// ═══════════════════════════════════════════════════════════════════
function toast(msg, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ═══════════════════════════════════════════════════════════════════
// Pipeline stage definitions
// ═══════════════════════════════════════════════════════════════════
const STAGES = [
  { id: "data_gathering",          name: "Data Gathering",            icon: "🔍" },
  { id: "data_validation",         name: "Data Validation",           icon: "✅" },
  { id: "kpi_extraction",          name: "KPI Extraction",            icon: "📊" },
  { id: "ratio_analysis",          name: "Ratio Analysis",            icon: "⚖️" },
  { id: "competitor_benchmarking", name: "Competitor Benchmarking",   icon: "🏆" },
  { id: "sentiment_analysis",      name: "Market Sentiment",          icon: "📰" },
  { id: "risk_detection",          name: "Risk Detection",            icon: "⚠️" },
  { id: "trend_analysis",          name: "Trend & Forecast",          icon: "📈" },
  { id: "recommendation",          name: "Recommendation",            icon: "🎯" },
];

// ═══════════════════════════════════════════════════════════════════
// Run Analysis
// ═══════════════════════════════════════════════════════════════════
async function runAnalysis() {
  const tickerInput = document.getElementById("ticker-input");
  const periodSelect = document.getElementById("period-select");
  const ticker = (tickerInput.value || "").trim().toUpperCase();
  const period = periodSelect.value;

  if (!ticker) {
    toast("Please enter a stock ticker symbol", "error");
    tickerInput.focus();
    return;
  }
  if (!/^[A-Z]{1,10}$/.test(ticker)) {
    toast("Invalid ticker. Use 1–10 letters (e.g. AAPL)", "error");
    return;
  }

  // Reset
  clearPoll();
  State.analysis = null;
  State.analysisId = null;

  // Show pipeline, hide results
  showSection("pipeline-section");
  hideSection("results-section");
  hideSection("empty-state");
  resetPipelineUI();

  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.innerHTML = `<span class="stage-spinner"></span> Analyzing...`;

  // Update last-updated
  document.getElementById("last-updated").textContent = new Date().toLocaleTimeString();

  try {
    const startResult = await API.post("/api/analysis/run", { ticker, period });
    State.analysisId = startResult.analysis_id;
    toast(`Analysis started for ${ticker}`, "info");
    startPolling();
  } catch (err) {
    toast(`Failed to start analysis: ${err.message}`, "error");
    btn.disabled = false;
    btn.innerHTML = `▶ Run Investment Analysis`;
  }
}

// ═══════════════════════════════════════════════════════════════════
// Polling
// ═══════════════════════════════════════════════════════════════════
function startPolling() {
  State.pollTimer = setInterval(async () => {
    try {
      const progress = await API.get(`/api/analysis/${State.analysisId}/progress`);
      updatePipelineProgress(progress.progress);

      if (progress.status !== "running") {
        clearPoll();
        const analysis = await API.get(`/api/analysis/${State.analysisId}`);
        State.analysis = analysis;

        if (analysis.status === "failed") {
          toast(`Analysis failed: ${analysis.error || "Unknown error"}`, "error");
          resetRunBtn();
          return;
        }

        renderResults(analysis);
        resetRunBtn();
        toast(`Analysis complete for ${analysis.ticker || ""}`, "success");
      }
    } catch (err) {
      // silent: will retry
    }
  }, 800);
}

function clearPoll() {
  if (State.pollTimer) {
    clearInterval(State.pollTimer);
    State.pollTimer = null;
  }
}

function resetRunBtn() {
  const btn = document.getElementById("run-btn");
  btn.disabled = false;
  btn.innerHTML = `▶ Run Investment Analysis`;
}

// ═══════════════════════════════════════════════════════════════════
// Pipeline UI
// ═══════════════════════════════════════════════════════════════════
function resetPipelineUI() {
  const container = document.getElementById("pipeline-grid");
  container.innerHTML = STAGES.map(stage => `
    <div class="pipeline-stage pending" id="stage-${stage.id}">
      <div class="stage-icon pending">${stage.icon}</div>
      <div class="stage-info">
        <div class="stage-name">${stage.name}</div>
        <div class="stage-meta" id="stage-meta-${stage.id}">Pending</div>
      </div>
    </div>
  `).join("");
}

function updatePipelineProgress(progressEvents) {
  if (!progressEvents) return;
  const latest = {};
  for (const event of progressEvents) {
    latest[event.stage_id] = event;
  }

  for (const [stageId, event] of Object.entries(latest)) {
    const el = document.getElementById(`stage-${stageId}`);
    const metaEl = document.getElementById(`stage-meta-${stageId}`);
    const iconEl = el?.querySelector(".stage-icon");
    if (!el) continue;

    el.className = `pipeline-stage ${event.status}`;
    iconEl.className = `stage-icon ${event.status}`;
    const stage = STAGES.find(s => s.id === stageId);

    if (event.status === "running") {
      iconEl.innerHTML = `<div class="stage-spinner" style="border-top-color:var(--accent)"></div>`;
      metaEl.textContent = "Running...";
    } else if (event.status === "completed") {
      iconEl.textContent = "✓";
      metaEl.textContent = event.message ? event.message.substring(0, 60) + (event.message.length > 60 ? "..." : "") : "Completed";
    } else if (event.status === "failed") {
      iconEl.textContent = "✗";
      metaEl.textContent = "Failed";
    }
  }
}

// ═══════════════════════════════════════════════════════════════════
// Render full results
// ═══════════════════════════════════════════════════════════════════
function renderResults(a) {
  showSection("results-section");

  // Demo badge
  const demoBadge = document.getElementById("results-demo-badge");
  if (a.is_demo) {
    demoBadge.style.display = "inline-flex";
  } else {
    demoBadge.style.display = "none";
  }

  renderHeroCard(a);
  renderKPICards(a);
  switchTab("overview");
  renderOverviewTab(a);
  renderFinancialsTab(a);
  renderRatiosTab(a);
  renderCompetitorsTab(a);
  renderSentimentTab(a);
  renderRisksTab(a);
  renderForecastTab(a);
  renderTraceTab(a);

  // Scroll to results
  document.getElementById("results-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ═══════════════════════════════════════════════════════════════════
// Hero recommendation card
// ═══════════════════════════════════════════════════════════════════
function renderHeroCard(a) {
  const c = a.company || {};
  const rec = a.recommendation || {};
  const risk = a.risk || {};
  const forecast = a.forecast || {};
  const kpis = a.kpis || {};

  const action = rec.action || "N/A";
  const actionClass = action.replace(" ", "-");
  const score = rec.score ?? "—";
  const confidence = rec.confidence ?? "—";
  const riskLevel = risk.level || "—";
  const riskScore = risk.score ?? "—";
  const outlook = forecast.outlook || "—";
  const outlookBadgeClass = outlook.includes("Bull") ? "bullish" : outlook.includes("Bear") ? "bearish" : "neutral-out";

  const price = a.current_price ? `$${fmt(a.current_price)}` : "—";
  const mktCap = a.market_cap ? `$${(a.market_cap / 1e9).toFixed(1)}B` : "—";
  const dq = a.data_quality ?? "—";

  document.getElementById("hero-card").innerHTML = `
    <div class="rec-card-hero">
      <div>
        <div class="rec-action ${actionClass}">${action}</div>
        <div style="margin-top:10px;font-size:12px;color:var(--text-muted);">AI Recommendation</div>
      </div>
      <div class="rec-company">
        <h2>${c.name || a.ticker || "—"} <span style="color:var(--accent);font-size:16px;">${a.ticker || ""}</span></h2>
        <p>${c.sector || ""} · ${c.industry || ""} · ${c.exchange || ""}</p>
        <p style="margin-top:4px;">Price: <b style="color:var(--text-primary);">${price}</b> &nbsp;|&nbsp; Market Cap: <b style="color:var(--text-primary);">${mktCap}</b> &nbsp;|&nbsp; CEO: ${c.ceo || "—"}</p>
        <p class="rec-ai-note">${(rec.key_reasons || [])[0] || ""}</p>
      </div>
      <div class="rec-metrics">
        <div class="rec-metric">
          <div class="val" style="color:var(--accent);">${score}<span style="font-size:13px;color:var(--text-muted);">/100</span></div>
          <div class="lbl">Investment Score</div>
        </div>
        <div class="rec-metric">
          <div class="val">${confidence}%</div>
          <div class="lbl">Confidence</div>
        </div>
        <div class="rec-metric">
          <div class="val">${riskScore}<span style="font-size:13px;color:var(--text-muted);">/100</span></div>
          <div class="lbl">Risk Score</div>
        </div>
        <div class="rec-metric">
          <span class="badge badge-${outlookBadgeClass}">${outlook}</span>
          <div class="lbl" style="margin-top:2px;">Outlook</div>
        </div>
        <div class="rec-metric">
          <div class="val" style="font-size:16px;">${dq}<span style="font-size:12px;color:var(--text-muted);">/100</span></div>
          <div class="lbl">Data Quality</div>
        </div>
      </div>
    </div>
    <div class="disclaimer-bar">
      ⚠️ <b>Disclaimer:</b> ${rec.disclaimer || "AI-generated analytical output for educational purposes only. Not financial advice."}
    </div>
  `;
}

// ═══════════════════════════════════════════════════════════════════
// KPI Cards
// ═══════════════════════════════════════════════════════════════════
function renderKPICards(a) {
  const kpis = a.kpis || {};

  const cards = [
    { key: "revenue", label: "Revenue", prefix: "$", suffix: "M", fmt: v => fmtM(v) },
    { key: "revenue_growth", label: "Revenue Growth", prefix: "", suffix: "%", fmt: v => fmt1(v) },
    { key: "eps", label: "EPS", prefix: "$", suffix: "", fmt: v => fmt2(v) },
    { key: "net_margin", label: "Net Margin", prefix: "", suffix: "%", fmt: v => fmt1(v) },
    { key: "operating_margin", label: "Op. Margin", prefix: "", suffix: "%", fmt: v => fmt1(v) },
    { key: "roe", label: "ROE", prefix: "", suffix: "%", fmt: v => fmt1(v) },
    { key: "pe", label: "P/E Ratio", prefix: "", suffix: "x", fmt: v => fmt1(v) },
    { key: "debt_to_equity", label: "Debt / Equity", prefix: "", suffix: "x", fmt: v => fmt2(v) },
    { key: "free_cash_flow", label: "Free Cash Flow", prefix: "$", suffix: "M", fmt: v => fmtM(v) },
    { key: "ebitda", label: "EBITDA", prefix: "$", suffix: "M", fmt: v => fmtM(v) },
    { key: "gross_margin", label: "Gross Margin", prefix: "", suffix: "%", fmt: v => fmt1(v) },
    { key: "market_cap", label: "Market Cap", prefix: "$", suffix: "B", fmt: v => fmt1(v) },
  ];

  const container = document.getElementById("kpi-cards");
  container.innerHTML = cards.map(c => {
    const kpi = kpis[c.key] || {};
    const val = kpi.value;
    const prev = kpi.prev;
    const change = kpi.change;
    const trend = kpi.trend || (change > 0 ? "improving" : change < 0 ? "deteriorating" : "stable");
    const displayVal = val !== null && val !== undefined
      ? `${c.prefix}${c.fmt(val)}${c.suffix}`
      : "—";
    const displayPrev = prev !== null && prev !== undefined
      ? `${c.prefix}${c.fmt(prev)}${c.suffix}`
      : "";

    let changeHtml = "";
    if (change !== null && change !== undefined) {
      const dir = change > 0 ? "up" : change < 0 ? "down" : "flat";
      const arrow = change > 0 ? "▲" : change < 0 ? "▼" : "—";
      changeHtml = `<div class="kpi-change ${dir}">${arrow} ${Math.abs(change).toFixed(1)}% vs prior</div>`;
    } else if (displayPrev) {
      changeHtml = `<div class="kpi-change flat" style="font-size:11px;">Prior: ${displayPrev}</div>`;
    }

    return `
      <div class="kpi-card">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value">${displayVal}</div>
        <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
          <div class="trend-dot ${trend}"></div>
          ${changeHtml}
        </div>
      </div>
    `;
  }).join("");
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Overview
// ═══════════════════════════════════════════════════════════════════
function renderOverviewTab(a) {
  const rec = a.recommendation || {};
  const cs = rec.component_scores || {};

  // Score breakdown
  let scoresHtml = Object.entries({
    "Financial Health": [cs.financial_health, "blue"],
    "Growth":           [cs.growth, "green"],
    "Valuation":        [cs.valuation, "blue"],
    "Competitive":      [cs.competitive, "cyan"],
    "Sentiment":        [cs.sentiment, "amber"],
    "Risk Profile":     [cs.risk, "green"],
  }).map(([label, [val, color]]) => {
    const pct = val !== undefined ? val.toFixed(0) : 0;
    return `
      <div class="score-row">
        <div class="score-label-col">${label}</div>
        <div class="score-bar-track">
          <div class="score-bar-fill ${color}" style="width:${pct}%"></div>
        </div>
        <div class="score-value-col">${pct}</div>
      </div>
    `;
  }).join("");

  // Key reasons + risks
  const reasons = (rec.key_reasons || []).map(r => `<div class="factor-item"><div class="dot" style="background:var(--green)"></div><span>${r}</span></div>`).join("");
  const risks = (rec.main_risks || []).map(r => `<div class="factor-item"><div class="dot" style="background:var(--red)"></div><span>${r}</span></div>`).join("");

  // Validation issues
  const issues = (a.validation_issues || []).slice(0, 5).map(i => `
    <div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px;">
      <span class="badge badge-${i.severity === 'high' ? 'high' : i.severity === 'warning' ? 'warning' : 'neutral'}">${i.severity}</span>
      <span style="color:var(--text-secondary)">${i.message}</span>
    </div>
  `).join("") || "<p style='font-size:13px;color:var(--green)'>No significant data quality issues detected.</p>";

  document.getElementById("tab-overview").innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="card">
        <div class="section-header">📊 Investment Score Breakdown</div>
        <div class="score-section">${scoresHtml}</div>
        <div style="margin-top:16px;font-size:24px;font-weight:800;color:var(--accent);">
          ${rec.score ?? "—"}<span style="font-size:14px;color:var(--text-muted);">/100 — ${rec.action || ""}</span>
        </div>
      </div>
      <div class="card">
        <div class="section-header">🎯 Key Reasons &amp; Risks</div>
        <h4 style="margin-bottom:8px;">Positive Factors</h4>
        <div class="factor-list">${reasons || "<p style='font-size:13px;color:var(--text-muted)'>None identified</p>"}</div>
        <h4 style="margin:14px 0 8px;">Risk Factors</h4>
        <div class="factor-list">${risks || "<p style='font-size:13px;color:var(--text-muted)'>None identified</p>"}</div>
      </div>
    </div>
    <div class="card" style="margin-top:0">
      <div class="section-header">🔬 Data Quality Validation</div>
      <p style="margin-bottom:12px;font-size:13px;">Data Quality Score: <b style="color:var(--text-primary);">${a.data_quality ?? "—"}/100</b> (${a.data_quality_label || "—"})</p>
      ${issues}
    </div>
    <div style="margin-top:16px;">
      ${renderPriceChart(a)}
    </div>
  `;

  // Draw price chart
  setTimeout(() => drawPriceChart(a), 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Financials
// ═══════════════════════════════════════════════════════════════════
function renderFinancialsTab(a) {
  const annual = a.annual_history || [];
  const years = annual.map(y => y.year);

  // fmtFin: format a raw-dollar value as $NNN,NNNm (millions, comma-separated integer)
  const fmtFin = v => {
    if (v === null || v === undefined) return "—";
    return Math.round(v / 1e6).toLocaleString("en-US");
  };

  const tableRows = annual.map(y => {
    const gm = y.revenue ? ((y.gross_profit / y.revenue) * 100).toFixed(1) : "—";
    const om = y.revenue ? ((y.operating_income / y.revenue) * 100).toFixed(1) : "—";
    const nm = y.revenue ? ((y.net_income / y.revenue) * 100).toFixed(1) : "—";
    const niColor = y.net_income >= 0 ? "var(--green)" : "var(--red)";
    return `
      <tr>
        <td>${y.year}</td>
        <td>$${fmtFin(y.revenue)}M</td>
        <td>$${fmtFin(y.gross_profit)}M</td>
        <td>$${fmtFin(y.operating_income)}M</td>
        <td style="color:${niColor}">$${fmtFin(y.net_income)}M</td>
        <td>${gm}%</td>
        <td>${om}%</td>
        <td>${nm}%</td>
        <td>${y.eps ?? "—"}</td>
        <td>$${fmtFin(y.ebitda)}M</td>
        <td style="color:${y.free_cash_flow >= 0 ? 'var(--green)' : 'var(--red)'}">$${fmtFin(y.free_cash_flow)}M</td>
      </tr>
    `;
  }).join("");

  document.getElementById("tab-financials").innerHTML = `
    <div class="chart-grid chart-grid-2" style="margin-bottom:16px;">
      <div class="chart-card">
        <div class="chart-title">📈 Revenue Trend ($M)</div>
        <div class="chart-container"><canvas id="chart-revenue"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">💰 Net Income Trend ($M)</div>
        <div class="chart-container"><canvas id="chart-netincome"></canvas></div>
      </div>
    </div>
    <div class="chart-grid chart-grid-2" style="margin-bottom:16px;">
      <div class="chart-card">
        <div class="chart-title">📊 Margin Trends (%)</div>
        <div class="chart-container"><canvas id="chart-margins"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">💵 EPS Trend ($)</div>
        <div class="chart-container"><canvas id="chart-eps"></canvas></div>
      </div>
    </div>
    <div class="card">
      <div class="section-header">📋 Annual Financial Summary</div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Year</th><th>Revenue</th><th>Gross Profit</th><th>Op. Income</th><th>Net Income</th>
            <th>GM%</th><th>OM%</th><th>NM%</th><th>EPS</th><th>EBITDA</th><th>FCF</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>
    </div>
  `;

  setTimeout(() => {
    drawLineChart("chart-revenue", years, [
      { label: "Revenue", data: a.kpi_history?.revenue || [], color: "#3b82f6" }
    ]);
    drawLineChart("chart-netincome", years, [
      { label: "Net Income", data: a.kpi_history?.net_income || [], color: "#22c55e" }
    ]);
    drawLineChart("chart-margins", years, [
      { label: "Gross Margin", data: a.kpi_history?.gross_margin || [], color: "#06b6d4" },
      { label: "Op. Margin",   data: a.kpi_history?.operating_margin || [], color: "#3b82f6" },
      { label: "Net Margin",   data: a.kpi_history?.net_margin || [], color: "#22c55e" },
    ]);
    drawLineChart("chart-eps", years, [
      { label: "EPS ($)", data: a.kpi_history?.eps || [], color: "#f59e0b" }
    ]);
  }, 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Ratios
// ═══════════════════════════════════════════════════════════════════
function renderRatiosTab(a) {
  const ratios = a.ratios || {};

  const groups = [
    { key: "profitability", title: "📈 Profitability", icon: "📈" },
    { key: "liquidity",     title: "💧 Liquidity",     icon: "💧" },
    { key: "leverage",      title: "🏋️ Leverage",      icon: "🏋️" },
    { key: "valuation",     title: "💲 Valuation",     icon: "💲" },
    { key: "growth",        title: "🚀 Growth",         icon: "🚀" },
  ];

  const groupsHtml = groups.map(g => {
    const group = ratios[g.key] || {};
    const rows = Object.entries(group).map(([key, item]) => {
      const val = item.value;
      const displayVal = val !== null && val !== undefined ? `${fmt2(val)}${item.unit || ""}` : "—";
      const prev = item.prev;
      const prevHtml = prev !== null && prev !== undefined ? `<div style="font-size:11px;color:var(--text-muted);">Prev: ${fmt2(prev)}${item.unit || ""}</div>` : "";
      return `
        <div class="ratio-row">
          <div>
            <div class="ratio-name">${humanize(key)}</div>
            <div class="ratio-interp">${item.interpretation || ""}</div>
          </div>
          <div class="ratio-value-block">
            <div class="ratio-value">${displayVal}</div>
            ${prevHtml}
          </div>
        </div>
      `;
    }).join("");

    return `
      <div class="ratio-group-card">
        <div class="ratio-group-title">${g.title}</div>
        ${rows}
      </div>
    `;
  }).join("");

  document.getElementById("tab-ratios").innerHTML = `
    <div class="ratio-grid">${groupsHtml}</div>
    <div class="chart-grid chart-grid-2" style="margin-top:16px;">
      <div class="chart-card">
        <div class="chart-title">📊 ROE Trend (%)</div>
        <div class="chart-container"><canvas id="chart-roe"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">💲 P/E Context</div>
        <div class="chart-container"><canvas id="chart-pe-context"></canvas></div>
      </div>
    </div>
  `;

  setTimeout(() => {
    const years = (a.kpi_history?.years || []);
    drawLineChart("chart-roe", years, [
      { label: "ROE (%)", data: a.kpi_history?.roe || [], color: "#8b5cf6" }
    ]);

    // PE context bar
    const pe = a.kpis?.pe?.value;
    if (pe) {
      drawBarChart("chart-pe-context",
        ["This Company", "Sector Avg (est.)", "Market Avg (est.)"],
        [pe, 22, 19],
        ["#3b82f6", "#64748b", "#94a3b8"]
      );
    }
  }, 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Competitors
// ═══════════════════════════════════════════════════════════════════
function renderCompetitorsTab(a) {
  const comp = a.competitor_analysis || {};
  const entities = comp.entities || [];
  const ticker = a.ticker;

  const tableRows = entities.map(e => {
    const isPrimary = e.is_primary;
    const cls = isPrimary ? "highlight" : "";
    const rev = e.revenue ? `$${(e.revenue / 1e9).toFixed(1)}B` : "—";
    const mktCap = e.market_cap ? `$${(e.market_cap / 1e9).toFixed(0)}B` : "—";

    return `
      <tr class="${cls}">
        <td><b>${e.ticker || "—"}</b>${isPrimary ? ' <span class="badge badge-running" style="font-size:9px;">YOU</span>' : ""}</td>
        <td>${e.name || "—"}</td>
        <td>${mktCap}</td>
        <td class="${colorClass(e.revenue_growth, 5, 0)}">${fmtPct(e.revenue_growth)}</td>
        <td class="${colorClass(e.net_margin, 15, 5)}">${fmtPct(e.net_margin)}</td>
        <td class="${colorClass(e.operating_margin, 15, 5)}">${fmtPct(e.operating_margin)}</td>
        <td class="${colorClass(e.roe, 15, 8)}">${fmtPct(e.roe)}</td>
        <td>${e.pe ? `${e.pe.toFixed(1)}x` : "—"}</td>
        <td class="${e.debt_to_equity > 2 ? 'text-red' : ''}">${e.debt_to_equity ? `${e.debt_to_equity.toFixed(2)}x` : "—"}</td>
        <td>${e.eps_growth !== undefined ? fmtPct(e.eps_growth) : "—"}</td>
        <td><b>${e.rank || "—"}</b></td>
        <td><b style="color:var(--accent)">${e.financial_score?.toFixed(0) ?? "—"}</b></td>
      </tr>
    `;
  }).join("");

  // Bar chart data for key metrics
  const labels = entities.map(e => e.ticker || "?");
  const netMargins = entities.map(e => e.net_margin ?? 0);
  const roeVals = entities.map(e => e.roe ?? 0);
  const barColors = entities.map(e => e.is_primary ? "#3b82f6" : "#374151");

  document.getElementById("tab-competitors").innerHTML = `
    <div class="card">
      <div class="section-header">🏆 Peer Comparison</div>
      <p style="margin-bottom:12px;font-size:13px;">
        <b>${a.ticker}</b> ranks <b>${comp.primary_rank ?? "—"}</b> of <b>${comp.total_peers ?? "—"}</b> peers
        with a financial health score of <b>${comp.primary_score?.toFixed(0) ?? "—"}/100</b>.
      </p>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Ticker</th><th>Name</th><th>Mkt Cap</th>
            <th>Rev Growth</th><th>Net Margin</th><th>Op. Margin</th><th>ROE</th>
            <th>P/E</th><th>D/E</th><th>EPS Growth</th>
            <th>Rank</th><th>Score</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>
    </div>
    <div class="chart-grid chart-grid-2" style="margin-top:16px;">
      <div class="chart-card">
        <div class="chart-title">💰 Net Margin Comparison (%)</div>
        <div class="chart-container"><canvas id="chart-comp-margin"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">📊 ROE Comparison (%)</div>
        <div class="chart-container"><canvas id="chart-comp-roe"></canvas></div>
      </div>
    </div>
  `;

  setTimeout(() => {
    drawBarChart("chart-comp-margin", labels, netMargins, barColors);
    drawBarChart("chart-comp-roe", labels, roeVals, barColors);
  }, 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Sentiment
// ═══════════════════════════════════════════════════════════════════
function renderSentimentTab(a) {
  const s = a.sentiment || {};
  const score = s.score ?? 0;
  const scoreColor = score > 10 ? "var(--green)" : score < -10 ? "var(--red)" : "var(--amber)";
  const posPct = s.positive_pct ?? 0;
  const negPct = s.negative_pct ?? 0;
  const neuPct = s.neutral_pct ?? 0;

  const topics = (s.top_topics || []).map(t => `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;">
      <span style="color:var(--text-secondary);">${t.topic}</span>
      <span class="badge badge-neutral">${t.count} articles</span>
    </div>
  `).join("");

  const headlines = (s.recent_headlines || []).map(n => {
    const sentClass = n.sentiment === "positive" ? "positive" : n.sentiment === "negative" ? "negative" : "neutral";
    return `
      <div class="news-item">
        <div>
          <span class="badge badge-${sentClass}" style="margin-bottom:4px;">${n.sentiment}</span>
          <div class="news-headline">${n.headline}</div>
          <div class="news-meta">${n.source || ""} · ${n.published_at || ""} · ${Array.isArray(n.topics) ? n.topics.join(", ") : (n.topic || "")}</div>
        </div>
      </div>
    `;
  }).join("");

  document.getElementById("tab-sentiment").innerHTML = `
    <div style="display:grid;grid-template-columns:280px 1fr;gap:16px;">
      <div>
        <div class="card">
          <div class="section-header">Sentiment Score</div>
          <div style="text-align:center;padding:16px 0;">
            <div class="sentiment-score-circle" style="background:${score > 0 ? 'var(--green-dim)' : score < 0 ? 'var(--red-dim)' : 'var(--amber-dim)'};color:${scoreColor};margin:0 auto 12px;">
              <div>${score > 0 ? "+" : ""}${score}</div>
              <div style="font-size:11px;font-weight:600">${s.label || ""}</div>
            </div>
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">${s.total_articles || 0} articles analyzed</div>
            <div class="sentiment-bar" style="display:flex;height:10px;border-radius:5px;overflow:hidden;gap:2px;">
              <div style="width:${posPct}%;background:var(--green);border-radius:5px 0 0 5px;" title="${posPct}% positive"></div>
              <div style="width:${neuPct}%;background:var(--text-muted);" title="${neuPct}% neutral"></div>
              <div style="width:${negPct}%;background:var(--red);border-radius:0 5px 5px 0;" title="${negPct}% negative"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:11px;">
              <span style="color:var(--green)">▲ ${posPct}%</span>
              <span style="color:var(--text-muted)">— ${neuPct}%</span>
              <span style="color:var(--red)">▼ ${negPct}%</span>
            </div>
          </div>
        </div>
        <div class="card" style="margin-top:0">
          <div class="section-header">Top Topics</div>
          ${topics || "<p style='font-size:13px;color:var(--text-muted)'>No topics identified</p>"}
        </div>
      </div>
      <div class="card" style="align-self:start">
        <div class="section-header">📰 Recent Headlines</div>
        ${headlines || "<p style='font-size:13px;color:var(--text-muted)'>No headlines available</p>"}
      </div>
    </div>
    <div class="chart-card" style="margin-top:16px;">
      <div class="chart-title">📊 Sentiment Breakdown</div>
      <div class="chart-container" style="height:200px;"><canvas id="chart-sentiment"></canvas></div>
    </div>
  `;

  setTimeout(() => {
    drawDoughnutChart("chart-sentiment",
      ["Positive", "Neutral", "Negative"],
      [posPct, neuPct, negPct],
      ["#22c55e", "#64748b", "#ef4444"]
    );
  }, 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Risks
// ═══════════════════════════════════════════════════════════════════
function renderRisksTab(a) {
  const risk = a.risk || {};
  const risks = risk.risks || [];
  const score = risk.score ?? 0;
  const level = risk.level || "—";

  const scoreColor = score > 75 ? "var(--red)" : score > 50 ? "#f97316" : score > 25 ? "var(--amber)" : "var(--green)";

  const riskItems = risks.map(r => `
    <div class="risk-item ${r.severity}">
      <div class="risk-header">
        <div class="risk-name">${r.name}</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="badge badge-${r.severity.toLowerCase()}">${r.severity}</span>
          <span style="font-size:12px;color:var(--text-muted);">Score: ${r.score}</span>
          <span style="font-size:11px;color:var(--text-muted);">Conf: ${r.confidence}%</span>
        </div>
      </div>
      <div class="risk-evidence">📌 ${r.evidence}</div>
      <div class="risk-impact">⚡ Impact: ${r.impact}</div>
    </div>
  `).join("");

  const riskCounts = {
    Critical: risks.filter(r => r.severity === "Critical").length,
    High:     risks.filter(r => r.severity === "High").length,
    Moderate: risks.filter(r => r.severity === "Moderate").length,
    Low:      risks.filter(r => r.severity === "Low").length,
  };

  document.getElementById("tab-risks").innerHTML = `
    <div style="display:grid;grid-template-columns:280px 1fr;gap:16px;">
      <div>
        <div class="card">
          <div class="section-header">Risk Profile</div>
          <div style="text-align:center;padding:16px 0;">
            <div style="font-size:48px;font-weight:800;color:${scoreColor};">${score}</div>
            <div style="font-size:12px;color:var(--text-muted);">/ 100</div>
            <div style="margin-top:8px;"><span class="badge badge-${level.toLowerCase()}" style="font-size:14px;padding:6px 14px;">${level} Risk</span></div>
          </div>
          <div class="score-section" style="margin-top:12px;">
            <div class="score-row">
              <div class="score-label-col" style="color:var(--red)">Critical</div>
              <div style="flex:1;font-weight:700;color:var(--red)">${riskCounts.Critical}</div>
            </div>
            <div class="score-row">
              <div class="score-label-col" style="color:var(--red)">High</div>
              <div style="flex:1;font-weight:700;">${riskCounts.High}</div>
            </div>
            <div class="score-row">
              <div class="score-label-col" style="color:var(--amber)">Moderate</div>
              <div style="flex:1;font-weight:700;">${riskCounts.Moderate}</div>
            </div>
            <div class="score-row">
              <div class="score-label-col" style="color:var(--green)">Low</div>
              <div style="flex:1;font-weight:700;">${riskCounts.Low}</div>
            </div>
          </div>
        </div>
        <div class="chart-card" style="margin-top:0">
          <div class="chart-title">Risk Distribution</div>
          <div class="chart-container" style="height:180px;"><canvas id="chart-risk-dist"></canvas></div>
        </div>
      </div>
      <div>
        <div class="section-header">⚠️ Detected Risk Factors (${risks.length})</div>
        <div class="risk-list">
          ${riskItems || "<p style='font-size:13px;color:var(--green)'>✓ No significant risk factors detected.</p>"}
        </div>
      </div>
    </div>
  `;

  setTimeout(() => {
    drawDoughnutChart("chart-risk-dist",
      ["Critical", "High", "Moderate", "Low"],
      [riskCounts.Critical, riskCounts.High, riskCounts.Moderate, riskCounts.Low],
      ["#7f1d1d", "#ef4444", "#f59e0b", "#22c55e"]
    );
  }, 100);
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Forecast
// ═══════════════════════════════════════════════════════════════════
function renderForecastTab(a) {
  const f = a.forecast || {};
  const trends = f.trends || {};
  const proj = f.projections || {};

  const outlookColor = (f.outlook || "").includes("Bull") ? "var(--green)"
    : (f.outlook || "").includes("Bear") ? "var(--red)" : "var(--amber)";

  const trendRows = Object.entries(trends).map(([key, t]) => {
    const dir = t.direction;
    const color = dir === "positive" ? "var(--green)" : dir === "negative" ? "var(--red)" : "var(--text-muted)";
    const arrow = dir === "positive" ? "▲" : dir === "negative" ? "▼" : "—";
    const avg = t.avg_growth_pct !== undefined ? `${t.avg_growth_pct > 0 ? "+" : ""}${t.avg_growth_pct?.toFixed(1)}%/yr` : (t.score !== undefined ? `Score: ${t.score}` : "");
    return `
      <tr>
        <td>${t.label || humanize(key)}</td>
        <td style="color:${color};font-weight:700;">${arrow} ${dir}</td>
        <td>${avg}</td>
      </tr>
    `;
  }).join("");

  const bullish = (f.bullish_factors || []).map(b =>
    `<div class="factor-item"><div class="dot" style="background:var(--green)"></div><span style="font-size:13px;color:var(--text-secondary);">${b}</span></div>`
  ).join("");
  const bearish = (f.bearish_factors || []).map(b =>
    `<div class="factor-item"><div class="dot" style="background:var(--red)"></div><span style="font-size:13px;color:var(--text-secondary);">${b}</span></div>`
  ).join("");

  document.getElementById("tab-forecast").innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
      <div class="card">
        <div class="section-header">🔮 Outlook</div>
        <div style="font-size:28px;font-weight:800;color:${outlookColor};margin-bottom:8px;">${f.outlook || "—"}</div>
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;">${f.outlook_note || ""}</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:12px;color:var(--text-muted);">Confidence:</span>
          <b style="color:var(--text-primary);">${f.confidence ?? "—"}%</b>
          <div class="score-bar-track" style="flex:1;height:6px;">
            <div class="score-bar-fill blue" style="width:${f.confidence ?? 0}%;"></div>
          </div>
        </div>
        <p style="margin-top:14px;font-size:11px;font-style:italic;color:var(--text-muted);">
          Based on ${proj.trend_basis || "historical data"}. ${proj.disclaimer || ""}
        </p>
      </div>
      <div class="card">
        <div class="section-header">📐 Trend Analysis</div>
        <table>
          <thead><tr><th>Indicator</th><th>Direction</th><th>Avg Change</th></tr></thead>
          <tbody>${trendRows}</tbody>
        </table>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
      <div class="card">
        <div class="section-header" style="color:var(--green);">🐂 Bullish Factors</div>
        <div class="factor-list">${bullish || "<p style='font-size:13px;color:var(--text-muted)'>None identified</p>"}</div>
      </div>
      <div class="card">
        <div class="section-header" style="color:var(--red);">🐻 Bearish Factors</div>
        <div class="factor-list">${bearish || "<p style='font-size:13px;color:var(--text-muted)'>None identified</p>"}</div>
      </div>
    </div>
    ${proj.revenue_next_year || proj.eps_next_year ? `
    <div class="card">
      <div class="section-header">📊 Trend-Based Projections <span class="badge badge-warning" style="margin-left:8px;">Not Financial Forecasts</span></div>
      <div style="display:flex;gap:32px;flex-wrap:wrap;">
        ${proj.revenue_next_year ? `
        <div>
          <div class="stat-lbl">Projected Revenue (Next Year)</div>
          <div class="stat-val" style="color:var(--accent);">$${fmtM(proj.revenue_next_year)}M</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Based on historical trend</div>
        </div>` : ""}
        ${proj.eps_next_year ? `
        <div>
          <div class="stat-lbl">Projected EPS (Next Year)</div>
          <div class="stat-val" style="color:var(--accent);">$${fmt2(proj.eps_next_year)}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Based on historical trend</div>
        </div>` : ""}
      </div>
      <p style="margin-top:12px;font-size:11px;color:var(--amber);font-style:italic;">⚠️ ${proj.disclaimer}</p>
    </div>` : ""}
  `;
}

// ═══════════════════════════════════════════════════════════════════
// Tab: Agent Trace
// ═══════════════════════════════════════════════════════════════════
function renderTraceTab(a) {
  const trace = a.agent_trace || [];

  const items = trace.map(t => `
    <div class="trace-item">
      <div class="trace-header" onclick="toggleTrace(this)">
        <span class="badge badge-${t.status}">${t.status}</span>
        <span class="trace-agent-name">${t.stage_name}</span>
        <span style="font-size:11px;color:var(--text-muted);">Agent: ${t.agent || "—"}</span>
        <span class="trace-time">⏱ ${t.execution_time?.toFixed(3) ?? "—"}s</span>
        <span class="trace-chevron">▼</span>
      </div>
      <div class="trace-body">
        <div class="trace-field">
          <div class="trace-field-label">Summary / Output</div>
          <div class="trace-field-value">${t.summary || "No summary available."}</div>
        </div>
        ${t.warnings?.length ? `
        <div class="trace-field">
          <div class="trace-field-label">Warnings</div>
          <div class="trace-field-value">${t.warnings.join("\n")}</div>
        </div>` : ""}
        ${t.error ? `
        <div class="trace-field">
          <div class="trace-field-label">Error</div>
          <div class="trace-field-value" style="color:var(--red);">${t.error}</div>
        </div>` : ""}
      </div>
    </div>
  `).join("");

  const totalTime = a.total_execution_time ?? 0;

  document.getElementById("tab-trace").innerHTML = `
    <div class="card" style="margin-bottom:16px;">
      <div class="section-header">⚙️ Pipeline Execution Summary</div>
      <div style="display:flex;gap:32px;flex-wrap:wrap;margin-bottom:12px;">
        <div>
          <div class="stat-lbl">Total Stages</div>
          <div class="stat-val">${trace.length}</div>
        </div>
        <div>
          <div class="stat-lbl">Completed</div>
          <div class="stat-val" style="color:var(--green)">${trace.filter(t=>t.status==="completed").length}</div>
        </div>
        <div>
          <div class="stat-lbl">Failed</div>
          <div class="stat-val" style="color:var(--red)">${trace.filter(t=>t.status==="failed").length}</div>
        </div>
        <div>
          <div class="stat-lbl">Total Time</div>
          <div class="stat-val">${totalTime.toFixed(2)}s</div>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Stage</th><th>Agent</th><th>Status</th><th>Time</th></tr></thead>
          <tbody>
            ${trace.map(t => `
              <tr>
                <td>${t.stage_name}</td>
                <td style="color:var(--text-muted);font-size:12px;">${t.agent || "—"}</td>
                <td><span class="badge badge-${t.status}">${t.status}</span></td>
                <td>${t.execution_time?.toFixed(3) ?? "—"}s</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="section-header">🔬 Agent Execution Detail</div>
      <p style="margin-bottom:14px;font-size:13px;color:var(--text-secondary);">
        Click each stage to expand input/output details and demonstrate the sequential agent architecture.
      </p>
      ${items}
    </div>
  `;
}

function toggleTrace(header) {
  header.classList.toggle("open");
  const body = header.nextElementSibling;
  body.classList.toggle("open");
}

// ═══════════════════════════════════════════════════════════════════
// Charting (using Chart.js via CDN)
// ═══════════════════════════════════════════════════════════════════

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: "#94a3b8", font: { size: 11 }, boxWidth: 12 }
    },
    tooltip: {
      backgroundColor: "#1c2230",
      borderColor: "#2d3748",
      borderWidth: 1,
      titleColor: "#e2e8f0",
      bodyColor: "#94a3b8",
    }
  },
  scales: {
    x: {
      ticks: { color: "#64748b", font: { size: 11 } },
      grid: { color: "rgba(45,55,72,0.6)" },
    },
    y: {
      ticks: { color: "#64748b", font: { size: 11 } },
      grid: { color: "rgba(45,55,72,0.6)" },
    },
  },
};

function destroyChart(id) {
  if (State.charts[id]) {
    State.charts[id].destroy();
    delete State.charts[id];
  }
}

function drawLineChart(canvasId, labels, datasets) {
  destroyChart(canvasId);
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  State.charts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: datasets.map(d => ({
        label: d.label,
        data: d.data,
        borderColor: d.color,
        backgroundColor: d.color + "22",
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: d.color,
        fill: datasets.length === 1,
        tension: 0.3,
      }))
    },
    options: { ...CHART_DEFAULTS },
  });
}

function drawBarChart(canvasId, labels, data, colors) {
  destroyChart(canvasId);
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  State.charts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || "#3b82f6",
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
    },
  });
}

function drawDoughnutChart(canvasId, labels, data, colors) {
  destroyChart(canvasId);
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  State.charts[canvasId] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 4 }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: { position: "right", labels: { color: "#94a3b8", font: { size: 11 }, boxWidth: 12 } },
        tooltip: CHART_DEFAULTS.plugins.tooltip,
      },
    },
  });
}

function renderPriceChart(a) {
  return `
    <div class="chart-card">
      <div class="chart-title">📈 Stock Price History (Weekly)</div>
      <div class="chart-container" style="height:260px;"><canvas id="chart-price"></canvas></div>
    </div>
  `;
}

function drawPriceChart(a) {
  const priceHistory = a.price_history || [];
  if (priceHistory.length === 0) return;

  // Sample every N points for readability
  const sample = priceHistory.filter((_, i) => i % 4 === 0 || i === priceHistory.length - 1);
  const labels = sample.map(p => p.date?.substring(5)); // MM-DD
  const closes = sample.map(p => p.close);

  destroyChart("chart-price");
  const canvas = document.getElementById("chart-price");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const gradient = ctx.createLinearGradient(0, 0, 0, 260);
  gradient.addColorStop(0, "rgba(59,130,246,0.3)");
  gradient.addColorStop(1, "rgba(59,130,246,0.0)");

  State.charts["chart-price"] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `${a.ticker} Price ($)`,
        data: closes,
        borderColor: "#3b82f6",
        backgroundColor: gradient,
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      }]
    },
    options: { ...CHART_DEFAULTS },
  });
}

// ═══════════════════════════════════════════════════════════════════
// Tab navigation
// ═══════════════════════════════════════════════════════════════════
function switchTab(tabId) {
  State.currentTab = tabId;
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === `tab-${tabId}`);
  });
}

// ═══════════════════════════════════════════════════════════════════
// Report download
// ═══════════════════════════════════════════════════════════════════
function downloadReport() {
  if (!State.analysisId) {
    toast("No analysis to report. Run an analysis first.", "error");
    return;
  }
  const url = `/api/analysis/${State.analysisId}/report?format=html`;
  window.open(url, "_blank");
  toast("Report opened in new tab. Use Print → Save as PDF.", "info");
}

// ═══════════════════════════════════════════════════════════════════
// Section visibility
// ═══════════════════════════════════════════════════════════════════
function showSection(id) { document.getElementById(id)?.style.setProperty("display", "block"); }
function hideSection(id) { document.getElementById(id)?.style.setProperty("display", "none"); }

// ═══════════════════════════════════════════════════════════════════
// Number formatting helpers
// ═══════════════════════════════════════════════════════════════════
function fmt(v)  { return v !== null && v !== undefined ? Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"; }
function fmt1(v) { return v !== null && v !== undefined ? Number(v).toFixed(1) : "—"; }
function fmt2(v) { return v !== null && v !== undefined ? Number(v).toFixed(2) : "—"; }
function fmtM(v) {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (Math.abs(n) >= 1000) return (n / 1000).toFixed(1) + "K";
  return n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function fmtPct(v) { return v !== null && v !== undefined ? `${Number(v).toFixed(1)}%` : "—"; }

function colorClass(v, good, warn) {
  if (v === null || v === undefined) return "";
  if (v >= good) return "text-green";
  if (v >= warn) return "";
  return "text-red";
}

function humanize(str) {
  return str.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
}

// ═══════════════════════════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  // Pipeline visibility: hide initially
  hideSection("pipeline-section");
  hideSection("results-section");

  // Load available tickers
  API.get("/api/companies").then(data => {
    const quickWrap = document.getElementById("quick-tickers");
    if (quickWrap && data.companies) {
      quickWrap.innerHTML = data.companies.map(c =>
        `<button class="quick-ticker-btn" onclick="setTicker('${c.ticker}')" title="${c.name}">${c.ticker}</button>`
      ).join("");
    }
  }).catch(() => {});

  // Enter key on ticker input
  const inp = document.getElementById("ticker-input");
  if (inp) {
    inp.addEventListener("keydown", e => {
      if (e.key === "Enter") runAnalysis();
    });
  }

  // Style color helpers via CSS
  const styleEl = document.createElement("style");
  styleEl.textContent = ".text-green{color:var(--green)!important}.text-red{color:var(--red)!important}";
  document.head.appendChild(styleEl);
});

function setTicker(ticker) {
  const inp = document.getElementById("ticker-input");
  if (inp) { inp.value = ticker; inp.focus(); }
}
