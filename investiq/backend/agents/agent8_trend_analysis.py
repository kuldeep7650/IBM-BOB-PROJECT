"""
Agent 8: Trend & Predictive Analysis Agent
Identifies historical trends and generates explainable forward-looking insights.
NOTE: All forecasts are analytical estimates based on historical patterns only.
      They do not constitute financial advice or guaranteed predictions.
"""

import time
from typing import Dict, Any, List, Optional


def _linear_trend(values: List[Optional[float]]) -> Optional[float]:
    """Return average period-over-period change (simple)."""
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return None
    diffs = [(clean[i] - clean[i-1]) / abs(clean[i-1]) * 100
             for i in range(1, len(clean)) if clean[i-1] != 0]
    return round(sum(diffs) / len(diffs), 2) if diffs else None


def _classify_trend(avg_change: Optional[float], positive_good: bool = True) -> str:
    if avg_change is None:
        return "stable"
    if positive_good:
        if avg_change > 3:
            return "positive"
        if avg_change < -3:
            return "negative"
    else:
        if avg_change < -3:
            return "positive"
        if avg_change > 3:
            return "negative"
    return "stable"


def run(risk_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = risk_data.get("output", {})
    kpi_history = data.get("kpi_history", {})
    kpis = data.get("kpis", {})
    risk = data.get("risk", {})
    sentiment = data.get("sentiment", {})
    competitor_analysis = data.get("competitor_analysis", {})
    price_history = data.get("financials", {}).get("price_history", [])

    def kv(key):
        return kpis.get(key, {}).get("value")

    # ── Historical trend analysis ────────────────────────────────────────────
    rev_trend = _linear_trend(kpi_history.get("revenue", []))
    eps_trend = _linear_trend(kpi_history.get("eps", []))
    margin_trend = _linear_trend(kpi_history.get("net_margin", []))
    roe_trend = _linear_trend(kpi_history.get("roe", []))
    ebitda_trend = _linear_trend(kpi_history.get("ebitda", []))

    # ── Price trend (last 12 weeks) ──────────────────────────────────────────
    price_trend = None
    price_volatility = None
    if len(price_history) >= 12:
        recent_prices = [p["close"] for p in price_history[-12:]]
        price_trend = _linear_trend(recent_prices)
        if len(recent_prices) > 1:
            avg = sum(recent_prices) / len(recent_prices)
            variance = sum((p - avg) ** 2 for p in recent_prices) / len(recent_prices)
            price_volatility = round((variance ** 0.5) / avg * 100, 2)

    # ── Trend classification ─────────────────────────────────────────────────
    trends = {
        "revenue": {
            "avg_growth_pct": rev_trend,
            "direction": _classify_trend(rev_trend),
            "label": "Revenue Trend",
        },
        "earnings": {
            "avg_growth_pct": eps_trend,
            "direction": _classify_trend(eps_trend),
            "label": "Earnings (EPS) Trend",
        },
        "margin": {
            "avg_growth_pct": margin_trend,
            "direction": _classify_trend(margin_trend),
            "label": "Net Margin Trend",
        },
        "roe": {
            "avg_growth_pct": roe_trend,
            "direction": _classify_trend(roe_trend),
            "label": "ROE Trend",
        },
        "price": {
            "avg_growth_pct": price_trend,
            "direction": _classify_trend(price_trend),
            "label": "Price Trend",
        },
        "sentiment": {
            "score": sentiment.get("score", 0),
            "direction": "positive" if sentiment.get("score", 0) > 10 else
                         "negative" if sentiment.get("score", 0) < -10 else "stable",
            "label": "Sentiment Trend",
        },
    }

    # ── Bullish / Bearish scoring ────────────────────────────────────────────
    bullish_factors = []
    bearish_factors = []

    # Revenue
    if rev_trend and rev_trend > 5:
        bullish_factors.append(f"Revenue CAGR trend of +{rev_trend:.1f}% indicates sustained top-line growth.")
    elif rev_trend and rev_trend < -2:
        bearish_factors.append(f"Revenue shrinking at {rev_trend:.1f}% average per year — demand concern.")

    # Earnings
    if eps_trend and eps_trend > 5:
        bullish_factors.append(f"EPS growing at +{eps_trend:.1f}% trend, indicating improving per-share value.")
    elif eps_trend and eps_trend < -2:
        bearish_factors.append(f"EPS declining at {eps_trend:.1f}% — earnings quality deteriorating.")

    # Margin
    if margin_trend and margin_trend > 0.5:
        bullish_factors.append("Net margins are expanding, suggesting improving operational efficiency.")
    elif margin_trend and margin_trend < -0.5:
        bearish_factors.append("Net margins compressing — cost pressures or pricing headwinds visible.")

    # ROE
    if roe_trend and roe_trend > 2:
        bullish_factors.append(f"ROE improving at +{roe_trend:.1f}% trend — capital efficiency is increasing.")
    elif roe_trend and roe_trend < -2:
        bearish_factors.append("ROE declining — returns on shareholder capital are eroding.")

    # Sentiment
    if sentiment.get("score", 0) > 20:
        bullish_factors.append("Positive news sentiment may support near-term investor appetite.")
    elif sentiment.get("score", 0) < -20:
        bearish_factors.append("Negative sentiment overhang may pressure valuation multiples.")

    # Risk
    risk_score = risk.get("score", 50)
    if risk_score < 30:
        bullish_factors.append("Risk profile is low — fundamental stability supports investment thesis.")
    elif risk_score > 60:
        bearish_factors.append(f"Risk score of {risk_score} is elevated — multiple headwinds present.")

    # Competitor position
    primary_rank = competitor_analysis.get("primary_rank", 3)
    total_peers = competitor_analysis.get("total_peers", 5)
    if primary_rank <= total_peers * 0.4:
        bullish_factors.append(f"Strong peer ranking ({primary_rank}/{total_peers}) vs. competitors.")
    elif primary_rank > total_peers * 0.6:
        bearish_factors.append(f"Below-average competitive position ({primary_rank}/{total_peers} peers).")

    # ── Outlook determination ─────────────────────────────────────────────────
    bull_count = len(bullish_factors)
    bear_count = len(bearish_factors)
    net = bull_count - bear_count

    if net >= 3:
        outlook = "Bullish"
        outlook_note = "Based on historical patterns, the company demonstrates multiple positive growth indicators."
    elif net >= 1:
        outlook = "Moderately Bullish"
        outlook_note = "Trend analysis suggests potential upside, though some headwinds remain."
    elif net <= -3:
        outlook = "Bearish"
        outlook_note = "Historical trends point to potential downside risk — caution is warranted."
    elif net <= -1:
        outlook = "Moderately Bearish"
        outlook_note = "Trend analysis suggests caution; more risks than tailwinds currently visible."
    else:
        outlook = "Neutral"
        outlook_note = "Mixed signals — bullish and bearish factors roughly balance out."

    # ── Confidence score ──────────────────────────────────────────────────────
    data_richness = min(100, len(data.get("annual_history", [])) * 15 + 25)
    signal_clarity = abs(net) / max(bull_count + bear_count, 1) * 100
    confidence = round((data_richness * 0.4 + signal_clarity * 0.6), 0)
    confidence = max(40, min(90, int(confidence)))

    # Simple next-year projection (trend-based, NOT a guarantee)
    rev = kv("revenue")
    projected_revenue = None
    if rev and rev_trend is not None:
        projected_revenue = round(rev * (1 + rev_trend / 100), 2)

    eps = kv("eps")
    projected_eps = None
    if eps and eps_trend is not None:
        projected_eps = round(eps * (1 + eps_trend / 100), 2)

    forecast = {
        "outlook": outlook,
        "outlook_note": outlook_note,
        "confidence": confidence,
        "bullish_factors": bullish_factors,
        "bearish_factors": bearish_factors,
        "trends": trends,
        "projections": {
            "disclaimer": (
                "Projections are based on historical trend extrapolation only. "
                "They do not account for unexpected macro events or company-specific changes. "
                "These are not financial forecasts."
            ),
            "revenue_next_year": projected_revenue,
            "eps_next_year": projected_eps,
            "trend_basis": f"{len(data.get('annual_history', []))} years of historical data",
        },
        "volatility": price_volatility,
    }

    out = data.copy()
    out["forecast"] = forecast

    return {
        "agent": "TrendPredictiveAnalysisAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [
            "Forecasts are analytical estimates based on historical patterns. "
            "Not financial advice."
        ],
        "output": out,
        "summary": (
            f"Outlook: {outlook} (confidence {confidence}%). "
            f"{bull_count} bullish / {bear_count} bearish factors identified. "
            f"{outlook_note}"
        ),
    }
