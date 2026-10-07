"""
Agent 5: Competitor Benchmarking Agent
Compares the selected company against peers using a configurable weighted scoring model.
"""

import time
from typing import Dict, Any, List, Optional

# ── Scoring weights (configurable) ───────────────────────────────────────────
SCORE_WEIGHTS = {
    "revenue_growth":    0.20,
    "net_margin":        0.20,
    "operating_margin":  0.15,
    "roe":               0.15,
    "roa":               0.10,
    "eps_growth":        0.10,
    "debt_to_equity":    0.10,   # lower is better
}

# Benchmarks for normalizing 0–100 score per metric
BENCHMARKS = {
    "revenue_growth":   {"min": -10, "max": 40},
    "net_margin":       {"min": 0, "max": 35},
    "operating_margin": {"min": 0, "max": 40},
    "roe":              {"min": 0, "max": 40},
    "roa":              {"min": 0, "max": 20},
    "eps_growth":       {"min": -20, "max": 50},
    "debt_to_equity":   {"min": 0, "max": 3},  # inverted
}


def _normalize(value: Optional[float], metric: str, invert: bool = False) -> float:
    """Map a raw metric value to a 0–100 score."""
    if value is None:
        return 50.0  # neutral default when data unavailable
    bm = BENCHMARKS.get(metric, {"min": 0, "max": 100})
    lo, hi = bm["min"], bm["max"]
    clamped = max(lo, min(hi, value))
    score = (clamped - lo) / (hi - lo) * 100
    return round(100 - score if invert else score, 2)


def _score_entity(entity: Dict) -> float:
    """Compute a single weighted financial health score for one entity."""
    total = 0.0
    for metric, weight in SCORE_WEIGHTS.items():
        val = entity.get(metric)
        invert = (metric == "debt_to_equity")
        total += _normalize(val, metric, invert=invert) * weight
    return round(total, 2)


def _rank_label(rank: int, total: int) -> str:
    if rank == 1:
        return "Best"
    if rank == total:
        return "Weakest"
    return f"Rank {rank}"


def run(ratio_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = ratio_data.get("output", {})
    ticker = data.get("ticker", "")
    company_info = data.get("company", {})
    kpis = data.get("kpis", {})
    competitors_raw = data.get("competitors", [])

    # Build the primary company entity
    def kv(key):
        kpi = kpis.get(key, {})
        return kpi.get("value")

    # kv("revenue") is in millions (from KPI extraction); convert to dollars to match peer format
    _rev_m = kv("revenue")
    primary = {
        "ticker": ticker,
        "name": company_info.get("name", ticker),
        "is_primary": True,
        "market_cap": data.get("financials", {}).get("market_cap", 0),
        "current_price": data.get("financials", {}).get("current_price", 0),
        "revenue": (_rev_m * 1_000_000) if _rev_m is not None else None,
        "revenue_growth": kv("revenue_growth"),
        "net_margin": kv("net_margin"),
        "operating_margin": kv("operating_margin"),
        "roe": kv("roe"),
        "roa": kv("roa"),
        "eps": kv("eps"),
        "eps_growth": kv("eps_growth"),
        "debt_to_equity": kv("debt_to_equity"),
        "pe": kv("pe"),
        "pb": kv("pb"),
        "ebitda": kv("ebitda"),
        "free_cash_flow": kv("free_cash_flow"),
    }

    # Combine primary + competitors
    all_entities = [primary] + [dict(c, is_primary=False) for c in competitors_raw[:5]]

    # Score each
    for entity in all_entities:
        entity["financial_score"] = _score_entity(entity)

    # Rank by score (descending)
    ranked = sorted(all_entities, key=lambda x: x["financial_score"], reverse=True)
    for i, entity in enumerate(ranked):
        entity["rank"] = i + 1
        entity["rank_label"] = _rank_label(i + 1, len(ranked))

    primary_entry = next((e for e in ranked if e.get("is_primary")), ranked[0])
    primary_rank = primary_entry["rank"]

    # Comparison table columns
    columns = [
        "ticker", "name", "revenue_growth", "net_margin", "operating_margin",
        "roe", "roa", "pe", "debt_to_equity", "eps_growth",
        "market_cap", "financial_score", "rank",
    ]

    comparison_table = [
        {col: entity.get(col) for col in columns}
        for entity in ranked
    ]

    # Best/weakest for each metric
    metric_leaders = {}
    for metric in SCORE_WEIGHTS.keys():
        valid = [(e["ticker"], e.get(metric)) for e in all_entities if e.get(metric) is not None]
        if valid:
            if metric == "debt_to_equity":
                best = min(valid, key=lambda x: x[1])
            else:
                best = max(valid, key=lambda x: x[1])
            metric_leaders[metric] = best[0]

    out = data.copy()
    out["competitor_analysis"] = {
        "entities": ranked,
        "comparison_table": comparison_table,
        "primary_rank": primary_rank,
        "total_peers": len(all_entities),
        "metric_leaders": metric_leaders,
        "primary_score": primary_entry["financial_score"],
        "best_score": ranked[0]["financial_score"],
        "worst_score": ranked[-1]["financial_score"],
    }

    peer_names = ", ".join(e["ticker"] for e in ranked if not e.get("is_primary"))
    summary = (
        f"{ticker} ranks {primary_rank} of {len(all_entities)} peers "
        f"(score {primary_entry['financial_score']:.0f}/100) "
        f"vs. peers: {peer_names}."
    )

    return {
        "agent": "CompetitorBenchmarkingAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [],
        "output": out,
        "summary": summary,
    }
