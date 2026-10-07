"""
InvestIQ Provider Abstraction Layer
Defines interfaces for data providers and selects real vs demo providers.
"""

import os
from typing import Dict, Any, List, Optional
from backend.providers.demo_data import (
    get_company_info as demo_company,
    get_financials as demo_financials,
    get_news as demo_news,
    get_competitors as demo_competitors,
    get_available_tickers as demo_tickers,
)


class MarketDataProvider:
    """Abstraction for market/price data."""

    def __init__(self, use_demo: bool = True):
        self.use_demo = use_demo
        self.api_key = os.getenv("MARKET_DATA_API_KEY", "")

    def get_price_history(self, ticker: str, period: str = "5y") -> List[Dict]:
        if self.use_demo or not self.api_key:
            from backend.providers.demo_data import get_price_history
            return get_price_history(ticker)
        # Placeholder for real API integration (e.g., Alpha Vantage, Polygon.io)
        raise NotImplementedError("Real market API not configured")


class FinancialDataProvider:
    """Abstraction for fundamental financial data."""

    def __init__(self, use_demo: bool = True):
        self.use_demo = use_demo
        self.api_key = os.getenv("FINANCIAL_DATA_API_KEY", "")

    def get_financials(self, ticker: str) -> Dict[str, Any]:
        if self.use_demo or not self.api_key:
            return demo_financials(ticker)
        # Placeholder for real API (e.g., Financial Modeling Prep, Polygon.io)
        raise NotImplementedError("Real financial API not configured")


class NewsDataProvider:
    """Abstraction for news and sentiment data."""

    def __init__(self, use_demo: bool = True):
        self.use_demo = use_demo
        self.api_key = os.getenv("NEWS_API_KEY", "")

    def get_news(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        if self.use_demo or not self.api_key:
            return demo_news(ticker)
        # Placeholder for real news API (e.g., NewsAPI.org, Benzinga)
        raise NotImplementedError("Real news API not configured")


class CompanyDataProvider:
    """Abstraction for company metadata."""

    def __init__(self, use_demo: bool = True):
        self.use_demo = use_demo

    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        if self.use_demo:
            return demo_company(ticker)
        # Placeholder for real company API
        raise NotImplementedError("Real company API not configured")

    def get_competitors(self, ticker: str) -> List[Dict[str, Any]]:
        if self.use_demo:
            return demo_competitors(ticker)
        raise NotImplementedError("Real competitor API not configured")

    def get_available_tickers(self) -> List[Dict[str, str]]:
        return demo_tickers()


def build_providers(force_demo: bool = False) -> Dict[str, Any]:
    """Build provider instances based on available API keys."""
    has_market_key = bool(os.getenv("MARKET_DATA_API_KEY"))
    has_financial_key = bool(os.getenv("FINANCIAL_DATA_API_KEY"))
    has_news_key = bool(os.getenv("NEWS_API_KEY"))

    use_demo = force_demo or not (has_market_key and has_financial_key and has_news_key)

    return {
        "market": MarketDataProvider(use_demo=True),      # Always demo for now
        "financial": FinancialDataProvider(use_demo=True),
        "news": NewsDataProvider(use_demo=True),
        "company": CompanyDataProvider(use_demo=True),
        "is_demo": True,
    }
