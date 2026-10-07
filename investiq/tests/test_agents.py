"""
InvestIQ — Basic Unit Tests
Tests core calculation logic without requiring Flask or external APIs.
"""

import sys
import os

# Ensure we can import from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Test data fixtures ────────────────────────────────────────────────────────

SAMPLE_ANNUAL = [
    {
        "year": 2020, "revenue": 200_000_000, "gross_profit": 80_000_000,
        "operating_income": 30_000_000, "net_income": 20_000_000, "eps": 2.0,
        "ebitda": 40_000_000, "free_cash_flow": 15_000_000,
        "total_debt": 50_000_000, "total_equity": 100_000_000,
        "current_assets": 60_000_000, "current_liabilities": 40_000_000,
    },
    {
        "year": 2021, "revenue": 240_000_000, "gross_profit": 100_000_000,
        "operating_income": 40_000_000, "net_income": 28_000_000, "eps": 2.8,
        "ebitda": 55_000_000, "free_cash_flow": 22_000_000,
        "total_debt": 45_000_000, "total_equity": 120_000_000,
        "current_assets": 80_000_000, "current_liabilities": 45_000_000,
    },
    {
        "year": 2022, "revenue": 280_000_000, "gross_profit": 120_000_000,
        "operating_income": 50_000_000, "net_income": 35_000_000, "eps": 3.5,
        "ebitda": 68_000_000, "free_cash_flow": 28_000_000,
        "total_debt": 40_000_000, "total_equity": 145_000_000,
        "current_assets": 100_000_000, "current_liabilities": 50_000_000,
    },
]

SAMPLE_FIN = {
    "ticker": "TEST",
    "currency": "USD",
    "annual": SAMPLE_ANNUAL,
    "current_price": 70.0,
    "market_cap": 700_000_000,
    "shares_outstanding": 10_000_000,
    "ratios": {"pe": 20.0, "pb": 4.8, "ev_ebitda": 12.0, "quick_ratio": 1.5},
    "price_history": [],
}

SAMPLE_COMPANY = {
    "name": "Test Corp", "ticker": "TEST", "sector": "Technology",
    "industry": "Software", "exchange": "NASDAQ", "currency": "USD",
    "description": "A test company.", "employees": 1000,
    "country": "USA", "ceo": "Jane Doe", "founded": 2000,
    "current_price": 70.0, "market_cap": 700_000_000, "beta": 1.1,
    "competitors": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_demo_data_returns_tickers():
    from backend.providers.demo_data import get_available_tickers
    tickers = get_available_tickers()
    assert len(tickers) >= 5
    symbols = [t["ticker"] for t in tickers]
    assert "AAPL" in symbols
    assert "MSFT" in symbols


def test_demo_data_financials():
    from backend.providers.demo_data import get_financials
    data = get_financials("AAPL")
    assert data is not None
    assert len(data["annual"]) >= 4
    assert data["current_price"] > 0


def test_demo_data_news():
    from backend.providers.demo_data import get_news
    news = get_news("AAPL")
    assert len(news) > 0
    for item in news:
        assert item["sentiment"] in ("positive", "neutral", "negative")


def test_agent1_data_gathering():
    from backend.providers import build_providers
    from backend.agents import agent1_data_gathering
    providers = build_providers()
    result = agent1_data_gathering.run("AAPL", providers)
    assert result["status"] == "completed"
    out = result["output"]
    assert out["ticker"] == "AAPL"
    assert len(out["annual_history"]) >= 3
    assert out["company"]["name"]


def test_agent2_validation():
    from backend.agents import agent1_data_gathering, agent2_data_validation
    from backend.providers import build_providers
    providers = build_providers()
    gathered = agent1_data_gathering.run("AAPL", providers)
    validated = agent2_data_validation.run(gathered)
    assert validated["status"] == "completed"
    score = validated["output"]["validation"]["score"]
    assert 0 <= score <= 100
    assert score > 70, f"Expected quality score > 70, got {score}"


def test_agent3_kpi_extraction():
    from backend.agents import agent3_kpi_extraction
    # Build a mock validated input
    validated = {
        "agent": "DataValidationAgent", "status": "completed",
        "output": {
            "ticker": "TEST",
            "company": SAMPLE_COMPANY,
            "financials": SAMPLE_FIN,
            "latest_annual": SAMPLE_ANNUAL[-1],
            "prev_annual": SAMPLE_ANNUAL[-2],
            "annual_history": SAMPLE_ANNUAL,
            "news": [],
            "competitors": [],
            "validation": {"score": 90, "label": "Excellent", "issues": []},
        }
    }
    result = agent3_kpi_extraction.run(validated)
    assert result["status"] == "completed"
    kpis = result["output"]["kpis"]

    # Revenue
    assert kpis["revenue"]["value"] == 280.0  # 280M
    # Gross margin ~42.86%
    assert abs(kpis["gross_margin"]["value"] - 42.86) < 1.0
    # Net margin ~12.5%
    assert abs(kpis["net_margin"]["value"] - 12.5) < 1.0
    # ROE ~24.1%
    assert kpis["roe"]["value"] > 20
    # EPS
    assert kpis["eps"]["value"] == 3.5
    # Revenue growth ~16.7% (280/240-1)
    rg = kpis["revenue_growth"]["value"]
    assert abs(rg - 16.67) < 1.0


def test_kpi_trend_labels():
    from backend.agents.agent3_kpi_extraction import _trend
    assert _trend(100, 90) == "improving"
    assert _trend(90, 100) == "deteriorating"
    assert _trend(100, 100) == "stable"
    assert _trend(None, 100) == "stable"


def test_agent4_ratio_analysis():
    from backend.agents import agent3_kpi_extraction, agent4_ratio_analysis
    validated = {
        "agent": "DataValidationAgent", "status": "completed",
        "output": {
            "ticker": "TEST", "company": SAMPLE_COMPANY,
            "financials": SAMPLE_FIN,
            "latest_annual": SAMPLE_ANNUAL[-1],
            "prev_annual": SAMPLE_ANNUAL[-2],
            "annual_history": SAMPLE_ANNUAL,
            "news": [], "competitors": [],
            "validation": {"score": 90, "label": "Excellent", "issues": []},
        }
    }
    kpi_result = agent3_kpi_extraction.run(validated)
    ratio_result = agent4_ratio_analysis.run(kpi_result)
    assert ratio_result["status"] == "completed"
    ratios = ratio_result["output"]["ratios"]
    assert "profitability" in ratios
    assert "liquidity" in ratios
    assert "leverage" in ratios
    assert "valuation" in ratios
    assert "growth" in ratios
    # Verify interpretation strings are present
    assert len(ratios["profitability"]["net_margin"]["interpretation"]) > 10


def test_agent6_sentiment():
    from backend.agents import agent6_sentiment_analysis
    mock_news = [
        {"headline": "Strong earnings beat", "sentiment": "positive", "topic": "Earnings", "source": "Reuters", "published_at": "2024-01-01"},
        {"headline": "CEO resigns amid scandal", "sentiment": "negative", "topic": "Management", "source": "CNBC", "published_at": "2024-01-02"},
        {"headline": "Company reports quarterly results", "sentiment": "neutral", "topic": "Earnings", "source": "WSJ", "published_at": "2024-01-03"},
        {"headline": "New product launch announced", "sentiment": "positive", "topic": "Product Launch", "source": "Bloomberg", "published_at": "2024-01-04"},
    ]
    mock_input = {
        "output": {
            "ticker": "TEST", "company": SAMPLE_COMPANY,
            "annual_history": SAMPLE_ANNUAL, "financials": SAMPLE_FIN,
            "news": mock_news, "competitors": [],
            "validation": {"score": 90, "label": "Excellent", "issues": []},
            "kpis": {}, "kpi_history": {},
        }
    }
    result = agent6_sentiment_analysis.run(mock_input)
    assert result["status"] == "completed"
    sentiment = result["output"]["sentiment"]
    assert sentiment["total_articles"] == 4
    assert sentiment["positive_count"] == 2
    assert sentiment["negative_count"] == 1
    assert sentiment["neutral_count"] == 1
    assert -100 <= sentiment["score"] <= 100


def test_agent7_risk_no_crash():
    from backend.agents import agent7_risk_detection
    # High-risk scenario
    mock_input = {
        "output": {
            "ticker": "TEST", "company": SAMPLE_COMPANY,
            "annual_history": SAMPLE_ANNUAL, "financials": SAMPLE_FIN,
            "news": [], "competitors": [],
            "validation": {"score": 70, "label": "Good", "issues": []},
            "kpis": {
                "revenue_growth": {"value": -5.0, "trend": "deteriorating"},
                "eps_growth": {"value": -10.0},
                "operating_margin": {"value": 10.0, "prev": 18.0, "trend": "deteriorating"},
                "debt_to_equity": {"value": 2.5},
                "current_ratio": {"value": 0.8},
                "pe": {"value": 45.0},
                "roe": {"value": 8.0, "prev": 15.0},
            },
            "kpi_history": {},
            "sentiment": {"score": -30, "label": "Negative", "negative_pct": 60},
            "competitor_analysis": {"primary_rank": 5, "total_peers": 5},
        }
    }
    result = agent7_risk_detection.run(mock_input)
    assert result["status"] == "completed"
    risk = result["output"]["risk"]
    assert risk["score"] >= 0
    assert risk["level"] in ("Low", "Moderate", "High", "Critical")
    # Should detect multiple risks
    assert len(risk["risks"]) >= 3


def test_agent9_recommendation_score_range():
    """Recommendation score must always be in [0, 100]."""
    from backend.agents import agent9_recommendation
    # Bullish scenario
    bull_input = _make_rec_input(rev_growth=20, eps_growth=15, roe=25, pe=22, de=0.5, sentiment_score=50, risk_score=20, rank=1, total=5, dq=92)
    r_bull = agent9_recommendation.run(bull_input)
    assert r_bull["status"] == "completed"
    score = r_bull["output"]["recommendation"]["score"]
    assert 0 <= score <= 100
    assert r_bull["output"]["recommendation"]["action"] in ("STRONG BUY", "BUY", "HOLD", "UNDERWEIGHT", "SELL")

    # Bearish scenario
    bear_input = _make_rec_input(rev_growth=-15, eps_growth=-20, roe=3, pe=80, de=3.5, sentiment_score=-60, risk_score=80, rank=5, total=5, dq=60)
    r_bear = agent9_recommendation.run(bear_input)
    score_bear = r_bear["output"]["recommendation"]["score"]
    assert 0 <= score_bear <= 100
    # Bearish should score lower than bullish
    assert score_bear < score


def _make_rec_input(rev_growth, eps_growth, roe, pe, de, sentiment_score, risk_score, rank, total, dq):
    return {
        "output": {
            "ticker": "TEST", "company": SAMPLE_COMPANY,
            "annual_history": SAMPLE_ANNUAL, "financials": SAMPLE_FIN,
            "news": [], "competitors": [],
            "validation": {"score": dq, "label": "Good", "issues": []},
            "kpis": {
                "revenue_growth": {"value": rev_growth},
                "eps_growth": {"value": eps_growth},
                "roe": {"value": roe, "prev": roe},
                "roa": {"value": roe * 0.5},
                "pe": {"value": pe},
                "pb": {"value": 4.0},
                "ev_ebitda": {"value": 15.0},
                "net_margin": {"value": 12.0, "prev": 10.0},
                "gross_margin": {"value": 42.0, "prev": 40.0},
                "operating_margin": {"value": 15.0, "prev": 18.0},
                "revenue": {"value": 280.0},
                "eps": {"value": 3.5, "prev": 3.0},
                "debt_to_equity": {"value": de},
                "current_ratio": {"value": 1.8},
                "free_cash_flow": {"value": 28.0},
                "ebitda": {"value": 68.0},
                "revenue_cagr": {"value": 10.0},
                "eps_cagr": {"value": 12.0},
                "market_cap": {"value": 0.7},
            },
            "kpi_history": {"years": [2020, 2021, 2022], "revenue": [200, 240, 280],
                            "eps": [2.0, 2.8, 3.5], "net_margin": [10, 11.67, 12.5],
                            "roe": [20, 23, 24], "ebitda": [40, 55, 68], "fcf": [15, 22, 28]},
            "sentiment": {"score": sentiment_score, "label": "Positive" if sentiment_score > 0 else "Negative"},
            "risk": {"score": risk_score, "level": "Moderate" if risk_score < 50 else "High", "risks": []},
            "forecast": {"outlook": "Bullish", "confidence": 70, "bullish_factors": [], "bearish_factors": []},
            "competitor_analysis": {"primary_rank": rank, "total_peers": total, "primary_score": 60, "entities": []},
            "ratios": {},
        }
    }


def test_data_validation_detects_issues():
    from backend.agents import agent2_data_validation
    # A gathered result with missing fields and negative equity
    bad_data = {
        "output": {
            "ticker": "BAD",
            "company": {},
            "financials": {"currency": "USD"},
            "latest_annual": {"revenue": 100_000_000, "net_income": -80_000_000,
                              "total_equity": -1_000_000},
            "prev_annual": {},
            "annual_history": [{"revenue": 100_000_000, "net_income": -80_000_000,
                                 "total_equity": -1_000_000}],
            "news": [],
            "competitors": [],
        }
    }
    result = agent2_data_validation.run(bad_data)
    assert result["status"] == "completed"
    score = result["output"]["validation"]["score"]
    issues = result["output"]["validation"]["issues"]
    assert score < 80
    assert len(issues) >= 3


# ─────────────────────────────────────────────────────────────────────────────
# Run manually
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    tests = [
        test_demo_data_returns_tickers,
        test_demo_data_financials,
        test_demo_data_news,
        test_agent1_data_gathering,
        test_agent2_validation,
        test_agent3_kpi_extraction,
        test_kpi_trend_labels,
        test_agent4_ratio_analysis,
        test_agent6_sentiment,
        test_agent7_risk_no_crash,
        test_agent9_recommendation_score_range,
        test_data_validation_detects_issues,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
