"""
Agent 1: Data Gathering Agent
Collects and normalizes company, financial, price, news and competitor data.
"""

import time
from typing import Dict, Any


def run(ticker: str, providers: Dict[str, Any], period: str = "5y") -> Dict[str, Any]:
    start = time.time()
    warnings = []

    company = providers["company"].get_company_info(ticker)
    financials = providers["financial"].get_financials(ticker)
    news = providers["news"].get_news(ticker)
    competitors_raw = providers["company"].get_competitors(ticker)

    if not financials or not financials.get("annual"):
        warnings.append("Financial data unavailable; using demo fallback")
        from backend.providers.demo_data import get_financials
        financials = get_financials(ticker)

    annual = financials.get("annual", [])
    latest = annual[-1] if annual else {}
    prev = annual[-2] if len(annual) >= 2 else {}

    # Derive revenue growth
    rev_growth = None
    if latest.get("revenue") and prev.get("revenue") and prev["revenue"] != 0:
        rev_growth = round((latest["revenue"] / prev["revenue"] - 1) * 100, 2)

    # Normalize
    normalized = {
        "ticker": ticker.upper(),
        "company": company,
        "financials": financials,
        "latest_annual": latest,
        "prev_annual": prev,
        "annual_history": annual,
        "revenue_growth": rev_growth,
        "news": news,
        "competitors": competitors_raw,
        "is_demo": providers.get("is_demo", True),
        "data_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "period": period,
    }

    return {
        "agent": "DataGatheringAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": warnings,
        "output": normalized,
        "summary": f"Gathered data for {company.get('name', ticker)}: "
                   f"{len(annual)} years of financials, "
                   f"{len(news)} news items, "
                   f"{len(competitors_raw)} competitors",
    }
