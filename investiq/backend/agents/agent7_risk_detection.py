"""
Agent 7: Risk Detection Agent
Identifies investment risks, scores severity and provides evidence-based explanations.
"""

import time
from typing import Dict, Any, List, Optional

RISK_WEIGHTS = {
    "margin_deterioration": 0.15,
    "high_debt":            0.15,
    "falling_revenue":      0.12,
    "falling_eps":          0.12,
    "high_valuation":       0.10,
    "negative_sentiment":   0.10,
    "competitive_pressure": 0.08,
    "regulatory_risk":      0.08,
    "market_volatility":    0.05,
    "liquidity_risk":       0.05,
}


def _severity(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Moderate"
    return "Low"


def run(sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = sentiment_data.get("output", {})
    kpis = data.get("kpis", {})
    sentiment = data.get("sentiment", {})
    annual = data.get("annual_history", [])
    fin = data.get("financials", {})
    competitor_analysis = data.get("competitor_analysis", {})

    def kv(key):
        return kpis.get(key, {}).get("value")

    def kt(key):
        return kpis.get(key, {}).get("trend", "stable")

    detected_risks: List[Dict] = []
    weighted_score = 0.0

    # ── 1. Margin Deterioration ───────────────────────────────────────────────
    om = kv("operating_margin")
    om_prev = kpis.get("operating_margin", {}).get("prev")
    om_trend = kt("operating_margin")
    if om is not None and om_trend == "deteriorating":
        severity_score = min(100, abs((om - om_prev) / (om_prev or 1)) * 300)
        detected_risks.append({
            "id": "margin_deterioration",
            "name": "Margin Compression",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": (
                f"Operating margin declined from {om_prev:.1f}% to {om:.1f}%, "
                f"a compression of {om_prev - om:.1f} percentage points."
            ),
            "impact": "Reduced profitability and potential downward pressure on earnings estimates.",
            "confidence": 85,
        })
        weighted_score += severity_score * RISK_WEIGHTS["margin_deterioration"]

    # ── 2. High Debt ──────────────────────────────────────────────────────────
    de = kv("debt_to_equity")
    if de is not None and de > 1.5:
        severity_score = min(100, (de - 1.5) / 1.5 * 100)
        detected_risks.append({
            "id": "high_debt",
            "name": "Elevated Leverage",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Debt-to-Equity ratio is {de:.2f}x, above the 1.5x threshold.",
            "impact": "Higher interest expense, refinancing risk, and reduced financial flexibility.",
            "confidence": 90,
        })
        weighted_score += severity_score * RISK_WEIGHTS["high_debt"]

    # ── 3. Falling Revenue ────────────────────────────────────────────────────
    rev_growth = kv("revenue_growth")
    if rev_growth is not None and rev_growth < 0:
        severity_score = min(100, abs(rev_growth) * 5)
        detected_risks.append({
            "id": "falling_revenue",
            "name": "Revenue Contraction",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Revenue declined by {abs(rev_growth):.1f}% year-over-year.",
            "impact": "May signal weakening demand, pricing pressure, or competitive displacement.",
            "confidence": 92,
        })
        weighted_score += severity_score * RISK_WEIGHTS["falling_revenue"]

    # ── 4. Falling EPS ────────────────────────────────────────────────────────
    eps_growth = kv("eps_growth")
    if eps_growth is not None and eps_growth < 0:
        severity_score = min(100, abs(eps_growth) * 4)
        detected_risks.append({
            "id": "falling_eps",
            "name": "EPS Deterioration",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"EPS declined by {abs(eps_growth):.1f}% year-over-year.",
            "impact": "Earnings decline may trigger valuation multiple compression.",
            "confidence": 88,
        })
        weighted_score += severity_score * RISK_WEIGHTS["falling_eps"]

    # ── 5. High Valuation ─────────────────────────────────────────────────────
    pe = kv("pe")
    if pe is not None and pe > 35:
        severity_score = min(100, (pe - 35) / 65 * 100)
        detected_risks.append({
            "id": "high_valuation",
            "name": "Premium Valuation Risk",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"P/E ratio of {pe:.1f}x is significantly above the 35x threshold.",
            "impact": "Elevated multiple leaves little room for disappointment; "
                      "any earnings miss could cause a sharp de-rating.",
            "confidence": 78,
        })
        weighted_score += severity_score * RISK_WEIGHTS["high_valuation"]

    # ── 6. Negative Sentiment ─────────────────────────────────────────────────
    sent_score = sentiment.get("score", 0)
    if sent_score < -10:
        severity_score = min(100, abs(sent_score))
        detected_risks.append({
            "id": "negative_sentiment",
            "name": "Negative Market Sentiment",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Sentiment score is {sent_score} ({sentiment.get('label', 'Negative')}). "
                        f"{sentiment.get('negative_pct', 0):.0f}% of recent news is negative.",
            "impact": "Negative news flow can suppress investor confidence and increase volatility.",
            "confidence": 70,
        })
        weighted_score += severity_score * RISK_WEIGHTS["negative_sentiment"]

    # ── 7. Competitive Pressure ───────────────────────────────────────────────
    primary_rank = competitor_analysis.get("primary_rank", 1)
    total_peers = competitor_analysis.get("total_peers", 1)
    if primary_rank and total_peers and primary_rank > total_peers * 0.6:
        severity_score = (primary_rank / total_peers) * 60
        detected_risks.append({
            "id": "competitive_pressure",
            "name": "Competitive Disadvantage",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Company ranks {primary_rank} of {total_peers} peers on composite financial health.",
            "impact": "Below-average competitive positioning may lead to market share erosion.",
            "confidence": 72,
        })
        weighted_score += severity_score * RISK_WEIGHTS["competitive_pressure"]

    # ── 8. Regulatory Risk (from news) ────────────────────────────────────────
    reg_news = [n for n in data.get("news", []) if "Regulation" in str(n.get("topic", "")) and n.get("sentiment") == "negative"]
    if len(reg_news) >= 2:
        severity_score = min(100, len(reg_news) * 20)
        detected_risks.append({
            "id": "regulatory_risk",
            "name": "Regulatory Exposure",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"{len(reg_news)} negative regulatory news items detected in recent coverage.",
            "impact": "Regulatory penalties, forced divestitures, or operational restrictions.",
            "confidence": 65,
        })
        weighted_score += severity_score * RISK_WEIGHTS["regulatory_risk"]

    # ── 9. Liquidity Risk ─────────────────────────────────────────────────────
    cr = kv("current_ratio")
    if cr is not None and cr < 1.0:
        severity_score = min(100, (1 - cr) * 100)
        detected_risks.append({
            "id": "liquidity_risk",
            "name": "Liquidity Concern",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Current ratio of {cr:.2f}x is below 1.0x, indicating current liabilities exceed current assets.",
            "impact": "Short-term cash flow stress; may require debt refinancing or asset sales.",
            "confidence": 85,
        })
        weighted_score += severity_score * RISK_WEIGHTS["liquidity_risk"]

    # ── 10. Market volatility (beta-based) ────────────────────────────────────
    beta = data.get("company", {}).get("beta", 1.0)
    if beta and beta > 1.5:
        severity_score = min(100, (beta - 1.5) * 40)
        detected_risks.append({
            "id": "market_volatility",
            "name": "High Market Volatility",
            "severity": _severity(severity_score),
            "score": round(severity_score),
            "evidence": f"Beta of {beta:.2f} indicates significantly above-market price volatility.",
            "impact": "Amplified drawdowns during market downturns; unsuitable for risk-averse portfolios.",
            "confidence": 80,
        })
        weighted_score += severity_score * RISK_WEIGHTS["market_volatility"]

    # ── Overall risk score ────────────────────────────────────────────────────
    risk_score = round(min(100, weighted_score))

    if risk_score <= 25:
        risk_level = "Low"
    elif risk_score <= 50:
        risk_level = "Moderate"
    elif risk_score <= 75:
        risk_level = "High"
    else:
        risk_level = "Critical"

    out = data.copy()
    out["risk"] = {
        "score": risk_score,
        "level": risk_level,
        "risks": sorted(detected_risks, key=lambda x: x["score"], reverse=True),
        "total_risks": len(detected_risks),
    }

    risk_names = [r["name"] for r in detected_risks[:3]]
    return {
        "agent": "RiskDetectionAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [],
        "output": out,
        "summary": (
            f"Risk score: {risk_score}/100 ({risk_level}). "
            f"{len(detected_risks)} risk factor(s) identified. "
            f"Top risks: {', '.join(risk_names) if risk_names else 'None detected'}."
        ),
    }
