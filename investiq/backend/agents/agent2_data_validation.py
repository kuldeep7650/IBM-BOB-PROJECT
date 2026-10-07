"""
Agent 2: Data Validation Agent
Validates gathered financial data and generates a quality score.
"""

import time
from typing import Dict, Any, List


def run(gathered: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    issues: List[Dict] = []
    score = 100

    data = gathered.get("output", {})
    annual = data.get("annual_history", [])
    latest = data.get("latest_annual", {})
    company = data.get("company", {})

    # ── Completeness checks ─────────────────────────────────────────────────
    required_fields = ["revenue", "gross_profit", "operating_income", "net_income",
                       "eps", "ebitda", "free_cash_flow", "total_debt", "total_equity"]

    for field in required_fields:
        if not latest.get(field) and latest.get(field) != 0:
            issues.append({"type": "missing", "field": field, "severity": "warning",
                           "message": f"Field '{field}' is missing in latest annual data"})
            score -= 3

    # ── Minimum data length ─────────────────────────────────────────────────
    if len(annual) < 3:
        issues.append({"type": "insufficient_history", "severity": "warning",
                       "message": f"Only {len(annual)} years of data available; 3+ recommended"})
        score -= 10

    # ── Negative equity check ────────────────────────────────────────────────
    if latest.get("total_equity", 1) <= 0:
        issues.append({"type": "negative_equity", "severity": "high",
                       "message": "Negative or zero stockholders' equity detected"})
        score -= 8

    # ── Margin sanity checks ─────────────────────────────────────────────────
    rev = latest.get("revenue", 1) or 1
    gp = latest.get("gross_profit", 0)
    ni = latest.get("net_income", 0)

    gross_margin = gp / rev
    if not (0 <= gross_margin <= 1):
        issues.append({"type": "invalid_ratio", "severity": "medium",
                       "message": f"Gross margin {gross_margin:.2%} is outside expected range [0%, 100%]"})
        score -= 5

    if ni / rev < -0.5:
        issues.append({"type": "extreme_loss", "severity": "medium",
                       "message": f"Net margin {ni/rev:.2%} indicates extreme losses"})
        score -= 5

    # ── Revenue consistency check ────────────────────────────────────────────
    revenues = [y.get("revenue", 0) for y in annual]
    for i in range(1, len(revenues)):
        if revenues[i-1] and abs(revenues[i] / revenues[i-1] - 1) > 0.8:
            issues.append({"type": "data_spike", "severity": "low",
                           "message": f"Unusually large revenue change between years {i-1} and {i}"})
            score -= 2

    # ── Company info completeness ────────────────────────────────────────────
    for f in ["name", "sector", "ceo"]:
        if not company.get(f):
            issues.append({"type": "missing_metadata", "field": f, "severity": "low",
                           "message": f"Company metadata '{f}' is missing"})
            score -= 1

    # ── News freshness ────────────────────────────────────────────────────────
    news = data.get("news", [])
    if len(news) < 5:
        issues.append({"type": "limited_news", "severity": "low",
                       "message": f"Only {len(news)} news items available; sentiment may be less reliable"})
        score -= 3

    # ── Currency check ────────────────────────────────────────────────────────
    currency = data.get("financials", {}).get("currency", "USD")
    if currency not in ["USD", "EUR", "GBP", "JPY", "CNY"]:
        issues.append({"type": "unknown_currency", "severity": "low",
                       "message": f"Unknown currency '{currency}'; conversion may not apply"})
        score -= 2

    score = max(0, min(100, score))

    # Determine quality label
    if score >= 90:
        quality_label = "Excellent"
    elif score >= 75:
        quality_label = "Good"
    elif score >= 60:
        quality_label = "Fair"
    else:
        quality_label = "Poor"

    # Pass through validated data unchanged (with metadata)
    validated_data = data.copy()
    validated_data["validation"] = {
        "score": score,
        "label": quality_label,
        "issues": issues,
        "issue_count": len(issues),
    }

    return {
        "agent": "DataValidationAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [i["message"] for i in issues if i["severity"] in ("warning", "high")],
        "output": validated_data,
        "summary": f"Data quality score: {score}/100 ({quality_label}). "
                   f"{len(issues)} validation issue(s) found.",
    }
