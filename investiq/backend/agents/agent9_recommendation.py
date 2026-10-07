"""
Agent 9: Investment Recommendation Agent
Generates the final investment recommendation with weighted scoring and explainability.
"""

import time
from typing import Dict, Any, List

# ── Configurable weights ──────────────────────────────────────────────────────
RECOMMENDATION_WEIGHTS = {
    "financial_health": 0.25,
    "growth":           0.20,
    "valuation":        0.15,
    "competitive":      0.15,
    "sentiment":        0.10,
    "risk":             0.15,
}

# ── Score → Action mapping ────────────────────────────────────────────────────
def _score_to_action(score: float) -> str:
    if score >= 80:
        return "STRONG BUY"
    if score >= 65:
        return "BUY"
    if score >= 50:
        return "HOLD"
    if score >= 35:
        return "UNDERWEIGHT"
    return "SELL"


def _score_financial_health(kpis: Dict, annual: list) -> float:
    """Score 0-100 for financial health."""
    score = 50.0

    def kv(key):
        return kpis.get(key, {}).get("value")

    # Net margin
    nm = kv("net_margin")
    if nm is not None:
        score += max(-20, min(20, (nm - 10) * 1.5))

    # ROE
    roe = kv("roe")
    if roe is not None:
        score += max(-15, min(15, (roe - 15) * 0.8))

    # Current ratio
    cr = kv("current_ratio")
    if cr is not None:
        score += max(-10, min(10, (cr - 1.5) * 8))

    # Free cash flow (positive = good)
    fcf = kv("free_cash_flow")
    if fcf is not None:
        score += 10 if fcf > 0 else -10

    return max(0, min(100, round(score, 1)))


def _score_growth(kpis: Dict) -> float:
    """Score 0-100 for growth."""
    score = 50.0

    def kv(key):
        return kpis.get(key, {}).get("value")

    rg = kv("revenue_growth")
    if rg is not None:
        score += max(-20, min(25, rg * 1.2))

    eg = kv("eps_growth")
    if eg is not None:
        score += max(-20, min(20, eg * 0.8))

    cagr = kv("revenue_cagr")
    if cagr is not None:
        score += max(-10, min(10, (cagr - 5) * 1.0))

    return max(0, min(100, round(score, 1)))


def _score_valuation(kpis: Dict) -> float:
    """Score 0-100 for valuation (lower PE/PB = better score)."""
    score = 50.0

    def kv(key):
        return kpis.get(key, {}).get("value")

    pe = kv("pe")
    if pe is not None:
        score += max(-25, min(20, (25 - pe) * 1.2))

    pb = kv("pb")
    if pb is not None:
        score += max(-15, min(15, (3 - pb) * 3))

    ev_ebitda = kv("ev_ebitda")
    if ev_ebitda is not None:
        score += max(-10, min(10, (15 - ev_ebitda) * 1.0))

    return max(0, min(100, round(score, 1)))


def _score_competitive(competitor_analysis: Dict) -> float:
    """Score 0-100 based on peer ranking."""
    rank = competitor_analysis.get("primary_rank", 3)
    total = competitor_analysis.get("total_peers", 5)
    primary_score = competitor_analysis.get("primary_score", 50)

    # Primary financial score is already 0-100
    # Boost/penalize based on rank
    rank_pct = (total - rank) / max(total - 1, 1)  # 1.0 = best, 0.0 = worst
    return round(0.6 * primary_score + 0.4 * rank_pct * 100, 1)


def _score_sentiment(sentiment: Dict) -> float:
    """Score 0-100 from sentiment score (-100 to +100)."""
    raw = sentiment.get("score", 0)
    return round(max(0, min(100, (raw + 100) / 2)), 1)


def _score_risk(risk: Dict) -> float:
    """Score 0-100 for risk (higher risk score = lower investment score)."""
    return round(max(0, 100 - risk.get("score", 50)), 1)


def run(trend_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = trend_data.get("output", {})
    kpis = data.get("kpis", {})
    annual = data.get("annual_history", [])
    sentiment = data.get("sentiment", {})
    risk = data.get("risk", {})
    forecast = data.get("forecast", {})
    competitor_analysis = data.get("competitor_analysis", {})
    company = data.get("company", {})
    ticker = data.get("ticker", "")

    # ── Component scores ──────────────────────────────────────────────────────
    financial_health_score = _score_financial_health(kpis, annual)
    growth_score = _score_growth(kpis)
    valuation_score = _score_valuation(kpis)
    competitive_score = _score_competitive(competitor_analysis)
    sentiment_score_val = _score_sentiment(sentiment)
    risk_score_val = _score_risk(risk)

    component_scores = {
        "financial_health": financial_health_score,
        "growth": growth_score,
        "valuation": valuation_score,
        "competitive": competitive_score,
        "sentiment": sentiment_score_val,
        "risk": risk_score_val,
    }

    # ── Weighted final score ──────────────────────────────────────────────────
    final_score = sum(
        component_scores[k] * v for k, v in RECOMMENDATION_WEIGHTS.items()
    )
    final_score = round(final_score, 1)
    action = _score_to_action(final_score)

    # ── Confidence ────────────────────────────────────────────────────────────
    data_quality_score = data.get("validation", {}).get("score", 80)
    forecast_confidence = forecast.get("confidence", 65)
    confidence = round((data_quality_score * 0.4 + forecast_confidence * 0.6))
    confidence = max(40, min(95, confidence))

    # ── Key reasons ────────────────────────────────────────────────────────────
    def kv(key):
        return kpis.get(key, {}).get("value")

    key_reasons: List[str] = []
    main_risks: List[str] = []

    # Positive reasons
    rev_growth = kv("revenue_growth")
    if rev_growth and rev_growth > 5:
        key_reasons.append(f"Revenue growth of {rev_growth:.1f}% demonstrates strong business momentum.")

    roe = kv("roe")
    if roe and roe > 15:
        key_reasons.append(f"ROE of {roe:.1f}% is above the 15% benchmark, indicating efficient capital use.")

    pe = kv("pe")
    if pe and pe < 25:
        key_reasons.append(f"P/E of {pe:.1f}x suggests reasonable valuation relative to earnings.")

    if sentiment.get("score", 0) > 15:
        key_reasons.append(f"Market sentiment is {sentiment.get('label', 'positive').lower()}, supporting investor confidence.")

    if forecast.get("outlook") in ("Bullish", "Moderately Bullish"):
        key_reasons.append(f"Historical trend analysis points to a {forecast['outlook'].lower()} outlook.")

    primary_rank = competitor_analysis.get("primary_rank", 3)
    total_peers = competitor_analysis.get("total_peers", 5)
    if primary_rank and total_peers and primary_rank <= 2:
        key_reasons.append(f"Top-{primary_rank} competitive position among {total_peers} peers.")

    de = kv("debt_to_equity")
    if de and de < 0.8:
        key_reasons.append(f"Debt/Equity of {de:.2f}x indicates conservative, manageable leverage.")

    # Negative / risk reasons
    if pe and pe > 35:
        main_risks.append(f"Valuation premium (P/E {pe:.1f}x) leaves limited margin of safety.")

    om = kv("operating_margin")
    om_prev = kpis.get("operating_margin", {}).get("prev")
    if om and om_prev and om < om_prev:
        main_risks.append(f"Operating margin declined from {om_prev:.1f}% to {om:.1f}%.")

    if risk.get("score", 0) > 50:
        main_risks.append(f"Risk score of {risk['score']}/100 ({risk.get('level')}) indicates meaningful headwinds.")

    if sentiment.get("score", 0) < -10:
        main_risks.append(f"Negative market sentiment ({sentiment.get('label')}) may suppress near-term performance.")

    if not key_reasons:
        key_reasons.append("Financial and operational metrics are broadly in line with sector expectations.")
    if not main_risks:
        main_risks.append("No major red flags detected in current data.")

    recommendation = {
        "action": action,
        "score": final_score,
        "confidence": confidence,
        "component_scores": component_scores,
        "weights": RECOMMENDATION_WEIGHTS,
        "key_reasons": key_reasons[:5],
        "main_risks": main_risks[:4],
        "disclaimer": (
            "This recommendation is generated by an AI analytical system using quantitative models. "
            "It is for educational and informational purposes only and does not constitute financial advice. "
            "Always conduct your own research or consult a qualified financial professional."
        ),
    }

    out = data.copy()
    out["recommendation"] = recommendation

    return {
        "agent": "InvestmentRecommendationAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [
            "AI-generated recommendation. Not financial advice. Past data does not guarantee future results."
        ],
        "output": out,
        "summary": (
            f"Recommendation: {action} | Score: {final_score}/100 | Confidence: {confidence}% | "
            f"Financial Health: {financial_health_score:.0f} | Growth: {growth_score:.0f} | "
            f"Valuation: {valuation_score:.0f} | Risk: {risk_score_val:.0f}"
        ),
    }
