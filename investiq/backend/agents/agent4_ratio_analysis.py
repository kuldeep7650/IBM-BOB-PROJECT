"""
Agent 4: Financial Ratio Analysis Agent
Calculates and interprets financial ratios with human-readable explanations.
"""

import time
from typing import Dict, Any, List, Optional


def _safe_div(a, b):
    try:
        return a / b if b else None
    except (TypeError, ZeroDivisionError):
        return None


def _interpret(name: str, value: Optional[float], prev: Optional[float] = None,
               sector: str = "Technology") -> str:
    """Generate a plain-English interpretation of a ratio."""
    if value is None:
        return "Insufficient data to interpret this ratio."

    benchmarks = {
        "gross_margin": 40, "operating_margin": 15, "net_margin": 10,
        "roe": 15, "roa": 5, "current_ratio": 1.5, "quick_ratio": 1.0,
        "debt_equity": 1.0, "debt_ebitda": 3.0, "pe": 25, "pb": 3.0,
        "ev_ebitda": 15, "revenue_cagr": 8, "eps_cagr": 10,
    }

    b = benchmarks.get(name, 0)
    direction = ""
    if prev and prev != 0:
        chg = (value - prev) / abs(prev) * 100
        if abs(chg) > 1:
            direction = f" (changed {chg:+.1f}% vs prior period)"

    intl = {
        "gross_margin": (
            f"Gross margin of {value:.1f}% {'is above' if value >= b else 'is below'} "
            f"the {b}% reference benchmark, indicating "
            f"{'strong' if value >= b else 'moderate'} pricing power and cost management."
        ),
        "operating_margin": (
            f"Operating margin of {value:.1f}%{direction}. "
            f"{'Above' if value >= b else 'Below'} the {b}% reference. "
            + ("Potential pressure on operating profitability." if (prev and value < prev) else "Operating efficiency appears solid.")
        ),
        "net_margin": (
            f"Net profit margin of {value:.1f}%{direction}. "
            f"{'Healthy profitability.' if value >= b else 'Margins are below peer benchmarks, warranting monitoring.'}"
        ),
        "roe": (
            f"Return on Equity of {value:.1f}%{direction}. "
            f"{'Above' if value >= b else 'Below'} the {b}% reference. "
            f"{'Strong capital efficiency.' if value >= b else 'Management may need to improve returns on shareholder capital.'}"
        ),
        "roa": (
            f"Return on Assets of {value:.1f}%{direction}. "
            f"{'Efficient use of assets.' if value >= b else 'Asset utilization could be improved.'}"
        ),
        "current_ratio": (
            f"Current ratio of {value:.2f}x indicates "
            f"{'adequate' if value >= b else 'potentially strained'} short-term liquidity. "
            f"Values below 1.0x signal potential difficulty meeting near-term obligations."
        ),
        "quick_ratio": (
            f"Quick ratio of {value:.2f}x suggests "
            f"{'solid' if value >= b else 'limited'} immediate liquidity excluding inventory."
        ),
        "debt_equity": (
            f"Debt-to-Equity of {value:.2f}x{direction}. "
            f"{'Leverage is elevated, increasing financial risk.' if value > b else 'Leverage is within manageable levels.'}"
        ),
        "debt_ebitda": (
            f"Debt/EBITDA of {value:.2f}x. "
            f"{'High leverage relative to earnings — debt repayment capacity may be limited.' if value > b else 'Debt is well-covered by operating earnings.'}"
        ),
        "pe": (
            f"P/E ratio of {value:.1f}x{direction}. "
            f"{'Premium valuation — high growth expectations are priced in.' if value > b else 'Valuation appears reasonable relative to earnings.'}"
        ),
        "pb": (
            f"P/B ratio of {value:.1f}x. "
            f"{'Significant premium over book value; justified only by strong returns.' if value > b else 'Modest premium over book value.'}"
        ),
        "ev_ebitda": (
            f"EV/EBITDA of {value:.1f}x. "
            f"{'Rich valuation on an enterprise basis.' if value > b else 'Reasonable enterprise valuation.'}"
        ),
        "revenue_cagr": (
            f"Revenue CAGR of {value:.1f}%{direction}. "
            f"{'Strong top-line growth trajectory.' if value >= b else 'Growth below sector expectations; expansion story may be maturing.'}"
        ),
        "eps_cagr": (
            f"EPS CAGR of {value:.1f}%{direction}. "
            f"{'Healthy earnings per share growth.' if value >= b else 'EPS growth is below typical expectations — watch for dilution or margin erosion.'}"
        ),
    }

    return intl.get(name, f"Value: {value:.2f}")


def run(kpi_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = kpi_data.get("output", {})
    kpis = data.get("kpis", {})
    annual = data.get("annual_history", [])
    sector = data.get("company", {}).get("sector", "Technology")
    ratios_raw = data.get("financials", {}).get("ratios", {})

    latest = annual[-1] if annual else {}
    prev = annual[-2] if len(annual) >= 2 else {}

    rev = latest.get("revenue", 1) or 1
    prev_rev = prev.get("revenue", 1) or 1

    def v(key):
        kpi = kpis.get(key, {})
        return kpi.get("value")

    def pv(key):
        kpi = kpis.get(key, {})
        return kpi.get("prev")

    # ── Profitability ────────────────────────────────────────────────────────
    profitability = {
        "gross_margin": {
            "value": v("gross_margin"), "prev": pv("gross_margin"),
            "unit": "%",
            "interpretation": _interpret("gross_margin", v("gross_margin"), pv("gross_margin"), sector),
        },
        "operating_margin": {
            "value": v("operating_margin"), "prev": pv("operating_margin"),
            "unit": "%",
            "interpretation": _interpret("operating_margin", v("operating_margin"), pv("operating_margin"), sector),
        },
        "net_margin": {
            "value": v("net_margin"), "prev": pv("net_margin"),
            "unit": "%",
            "interpretation": _interpret("net_margin", v("net_margin"), pv("net_margin"), sector),
        },
        "roe": {
            "value": v("roe"), "prev": pv("roe"),
            "unit": "%",
            "interpretation": _interpret("roe", v("roe"), pv("roe"), sector),
        },
        "roa": {
            "value": v("roa"), "unit": "%",
            "interpretation": _interpret("roa", v("roa"), None, sector),
        },
    }

    # ── Liquidity ────────────────────────────────────────────────────────────
    current_ratio = v("current_ratio")
    quick = ratios_raw.get("quick_ratio")
    liquidity = {
        "current_ratio": {
            "value": current_ratio, "unit": "x",
            "interpretation": _interpret("current_ratio", current_ratio, None, sector),
        },
        "quick_ratio": {
            "value": quick, "unit": "x",
            "interpretation": _interpret("quick_ratio", quick, None, sector),
        },
    }

    # ── Leverage ─────────────────────────────────────────────────────────────
    de = v("debt_to_equity")
    ebitda = latest.get("ebitda") or 1
    debt = latest.get("total_debt", 0)
    debt_ebitda = _safe_div(debt, ebitda)
    leverage = {
        "debt_to_equity": {
            "value": de, "unit": "x",
            "interpretation": _interpret("debt_equity", de, None, sector),
        },
        "debt_to_ebitda": {
            "value": round(debt_ebitda, 2) if debt_ebitda else None, "unit": "x",
            "interpretation": _interpret("debt_ebitda", debt_ebitda, None, sector),
        },
    }

    # ── Valuation ────────────────────────────────────────────────────────────
    pe = v("pe")
    pb = v("pb")
    ev_ebitda = v("ev_ebitda")
    valuation = {
        "pe": {
            "value": pe, "unit": "x",
            "interpretation": _interpret("pe", pe, None, sector),
        },
        "pb": {
            "value": pb, "unit": "x",
            "interpretation": _interpret("pb", pb, None, sector),
        },
        "ev_ebitda": {
            "value": ev_ebitda, "unit": "x",
            "interpretation": _interpret("ev_ebitda", ev_ebitda, None, sector),
        },
    }

    # ── Growth ───────────────────────────────────────────────────────────────
    growth = {
        "revenue_cagr": {
            "value": v("revenue_cagr"), "unit": "%",
            "interpretation": _interpret("revenue_cagr", v("revenue_cagr"), None, sector),
        },
        "eps_cagr": {
            "value": v("eps_cagr"), "unit": "%",
            "interpretation": _interpret("eps_cagr", v("eps_cagr"), None, sector),
        },
        "revenue_growth_yoy": {
            "value": v("revenue_growth"), "unit": "%",
            "interpretation": (
                f"Year-over-year revenue growth of {v('revenue_growth'):.1f}%."
                if v("revenue_growth") is not None else "N/A"
            ),
        },
    }

    ratio_output = {
        "profitability": profitability,
        "liquidity": liquidity,
        "leverage": leverage,
        "valuation": valuation,
        "growth": growth,
    }

    out = data.copy()
    out["ratios"] = ratio_output

    # Build interpretation list for summary
    key_findings = []
    if v("operating_margin") and pv("operating_margin") and v("operating_margin") < pv("operating_margin"):
        key_findings.append(
            f"Operating margin declined from {pv('operating_margin'):.1f}% to "
            f"{v('operating_margin'):.1f}%, indicating potential pressure on profitability."
        )
    if pe and pe > 30:
        key_findings.append(f"P/E of {pe:.1f}x reflects premium growth expectations.")
    if de and de > 1.5:
        key_findings.append(f"Debt/Equity of {de:.2f}x is elevated — monitor leverage.")
    if v("roe") and v("roe") > 20:
        key_findings.append(f"ROE of {v('roe'):.1f}% demonstrates strong capital efficiency.")

    return {
        "agent": "FinancialRatioAnalysisAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [],
        "output": out,
        "summary": "; ".join(key_findings) if key_findings else "Financial ratios calculated successfully.",
    }
