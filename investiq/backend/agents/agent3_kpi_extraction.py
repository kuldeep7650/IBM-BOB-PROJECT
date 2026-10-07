"""
Agent 3: KPI Extraction Agent
Extracts, normalizes and trend-labels key financial KPIs.
"""

import time
from typing import Dict, Any, List, Optional


def _safe_div(a, b, default=None):
    try:
        return a / b if b else default
    except (TypeError, ZeroDivisionError):
        return default


def _trend(current, previous) -> str:
    if current is None or previous is None or previous == 0:
        return "stable"
    change = (current - previous) / abs(previous)
    if change > 0.02:
        return "improving"
    if change < -0.02:
        return "deteriorating"
    return "stable"


def _pct_change(current, previous) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 2)


def _fmt_millions(v) -> Optional[float]:
    if v is None:
        return None
    return round(v / 1_000_000, 2)


def run(validated: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = validated.get("output", {})
    annual = data.get("annual_history", [])

    latest = annual[-1] if annual else {}
    prev = annual[-2] if len(annual) >= 2 else {}
    prev2 = annual[-3] if len(annual) >= 3 else {}

    rev = latest.get("revenue", 0)
    prev_rev = prev.get("revenue", 0)
    gp = latest.get("gross_profit", 0)
    oi = latest.get("operating_income", 0)
    ni = latest.get("net_income", 0)
    eps = latest.get("eps", 0)
    prev_eps = prev.get("eps", 0)
    ebitda = latest.get("ebitda", 0)
    fcf = latest.get("free_cash_flow", 0)
    debt = latest.get("total_debt", 0)
    equity = latest.get("total_equity", 1)
    ca = latest.get("current_assets", 0)
    cl = latest.get("current_liabilities", 1)

    fin_meta = data.get("financials", {})
    mkt_cap = fin_meta.get("market_cap", 0)
    shares = fin_meta.get("shares_outstanding", 1)
    current_price = fin_meta.get("current_price", 0)
    ratios_raw = fin_meta.get("ratios", {})

    # ── KPI Calculations ─────────────────────────────────────────────────────
    gross_margin = _safe_div(gp, rev)
    operating_margin = _safe_div(oi, rev)
    net_margin = _safe_div(ni, rev)
    roe = _safe_div(ni, equity)
    total_assets = equity + debt  # simplified
    roa = _safe_div(ni, total_assets)
    debt_equity = _safe_div(debt, equity)
    current_ratio = _safe_div(ca, cl)
    pe = ratios_raw.get("pe") or _safe_div(current_price, eps)
    pb = ratios_raw.get("pb") or _safe_div(current_price * shares, equity)
    ev_ebitda = ratios_raw.get("ev_ebitda")

    rev_growth = _pct_change(rev, prev_rev)
    eps_growth = _pct_change(eps, prev_eps)

    # Revenue CAGR (3y or 5y)
    oldest = annual[0] if annual else {}
    n_years = len(annual) - 1
    rev_cagr = None
    if oldest.get("revenue") and rev and n_years > 0:
        rev_cagr = round((pow(rev / oldest["revenue"], 1 / n_years) - 1) * 100, 2)

    # EPS CAGR
    oldest_eps = oldest.get("eps")
    eps_cagr = None
    if oldest_eps and eps and oldest_eps != 0 and n_years > 0:
        try:
            eps_cagr = round((pow(abs(eps) / abs(oldest_eps), 1 / n_years) - 1) * 100, 2)
        except Exception:
            pass

    prev_gm = _safe_div(prev.get("gross_profit", 0), prev.get("revenue", 1))
    prev_om = _safe_div(prev.get("operating_income", 0), prev.get("revenue", 1))
    prev_nm = _safe_div(prev.get("net_income", 0), prev.get("revenue", 1))
    prev_roe = _safe_div(prev.get("net_income", 0), prev.get("total_equity", 1))

    kpis = {
        "revenue": {
            "value": _fmt_millions(rev),
            "prev": _fmt_millions(prev_rev),
            "change": rev_growth,
            "trend": _trend(rev, prev_rev),
            "unit": "M USD",
        },
        "revenue_growth": {
            "value": rev_growth,
            "trend": _trend(rev_growth, _pct_change(prev_rev, prev2.get("revenue"))),
            "unit": "%",
        },
        "gross_profit": {"value": _fmt_millions(gp), "unit": "M USD",
                         "prev": _fmt_millions(prev.get("gross_profit"))},
        "gross_margin": {
            "value": round(gross_margin * 100, 2) if gross_margin is not None else None,
            "prev": round(prev_gm * 100, 2) if prev_gm is not None else None,
            "trend": _trend(gross_margin, prev_gm),
            "unit": "%",
        },
        "operating_income": {"value": _fmt_millions(oi), "unit": "M USD"},
        "operating_margin": {
            "value": round(operating_margin * 100, 2) if operating_margin is not None else None,
            "prev": round(prev_om * 100, 2) if prev_om is not None else None,
            "trend": _trend(operating_margin, prev_om),
            "unit": "%",
        },
        "net_income": {"value": _fmt_millions(ni), "unit": "M USD"},
        "net_margin": {
            "value": round(net_margin * 100, 2) if net_margin is not None else None,
            "prev": round(prev_nm * 100, 2) if prev_nm is not None else None,
            "trend": _trend(net_margin, prev_nm),
            "unit": "%",
        },
        "eps": {
            "value": eps,
            "prev": prev_eps,
            "change": eps_growth,
            "trend": _trend(eps, prev_eps),
            "unit": "USD",
        },
        "eps_growth": {"value": eps_growth, "unit": "%"},
        "ebitda": {"value": _fmt_millions(ebitda), "unit": "M USD"},
        "free_cash_flow": {"value": _fmt_millions(fcf), "unit": "M USD",
                           "trend": _trend(fcf, prev.get("free_cash_flow"))},
        "roe": {
            "value": round(roe * 100, 2) if roe is not None else None,
            "prev": round(prev_roe * 100, 2) if prev_roe is not None else None,
            "trend": _trend(roe, prev_roe),
            "unit": "%",
        },
        "roa": {
            "value": round(roa * 100, 2) if roa is not None else None,
            "unit": "%",
        },
        "debt_to_equity": {
            "value": round(debt_equity, 3) if debt_equity is not None else None,
            "unit": "x",
            "trend": "deteriorating" if debt_equity and debt_equity > 2 else
                     "improving" if debt_equity and debt_equity < 0.5 else "stable",
        },
        "current_ratio": {
            "value": round(current_ratio, 2) if current_ratio is not None else None,
            "unit": "x",
        },
        "pe": {
            "value": round(pe, 2) if pe is not None else None,
            "unit": "x",
        },
        "pb": {
            "value": round(pb, 2) if pb is not None else None,
            "unit": "x",
        },
        "ev_ebitda": {
            "value": round(ev_ebitda, 2) if ev_ebitda is not None else None,
            "unit": "x",
        },
        "market_cap": {
            "value": round(mkt_cap / 1_000_000_000, 2) if mkt_cap else None,
            "unit": "B USD",
        },
        "revenue_cagr": {"value": rev_cagr, "unit": "%"},
        "eps_cagr": {"value": eps_cagr, "unit": "%"},
    }

    # Historical series for charts
    history = {
        "years": [y["year"] for y in annual],
        "revenue": [_fmt_millions(y.get("revenue")) for y in annual],
        "net_income": [_fmt_millions(y.get("net_income")) for y in annual],
        "eps": [y.get("eps") for y in annual],
        "gross_margin": [round(_safe_div(y.get("gross_profit", 0), y.get("revenue", 1)) * 100, 2) for y in annual],
        "operating_margin": [round(_safe_div(y.get("operating_income", 0), y.get("revenue", 1)) * 100, 2) for y in annual],
        "net_margin": [round(_safe_div(y.get("net_income", 0), y.get("revenue", 1)) * 100, 2) for y in annual],
        "roe": [round(_safe_div(y.get("net_income", 0), y.get("total_equity", 1)) * 100, 2) for y in annual],
        "fcf": [_fmt_millions(y.get("free_cash_flow")) for y in annual],
        "ebitda": [_fmt_millions(y.get("ebitda")) for y in annual],
    }

    out = data.copy()
    out["kpis"] = kpis
    out["kpi_history"] = history

    return {
        "agent": "KPIExtractionAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [],
        "output": out,
        "summary": (
            f"Revenue: ${_fmt_millions(rev):,.0f}M | "
            f"Net Margin: {round(net_margin*100,1) if net_margin else 'N/A'}% | "
            f"EPS: ${eps} | ROE: {round(roe*100,1) if roe else 'N/A'}%"
        ),
    }
