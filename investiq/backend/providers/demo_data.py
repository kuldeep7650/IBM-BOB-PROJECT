"""
InvestIQ Demo Data Provider
Provides realistic mock financial data for 5 companies when real APIs are unavailable.
All data is clearly labeled as DEMO DATA and is not real-time market data.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

# ─── Company Universe ────────────────────────────────────────────────────────

DEMO_COMPANIES = {
    "AAPL": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NASDAQ",
        "currency": "USD",
        "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
        "employees": 164000,
        "country": "United States",
        "website": "https://www.apple.com",
        "ceo": "Tim Cook",
        "founded": 1976,
        "competitors": ["MSFT", "GOOGL", "SAMSUNG_KS", "META", "AMZN"],
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Technology",
        "industry": "Software — Infrastructure",
        "exchange": "NASDAQ",
        "currency": "USD",
        "description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
        "employees": 221000,
        "country": "United States",
        "website": "https://www.microsoft.com",
        "ceo": "Satya Nadella",
        "founded": 1975,
        "competitors": ["AAPL", "GOOGL", "AMZN", "ORCL", "CRM"],
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "sector": "Technology",
        "industry": "Internet Content & Information",
        "exchange": "NASDAQ",
        "currency": "USD",
        "description": "Alphabet Inc. provides online advertising services, cloud computing, search engine technology, and AI services globally.",
        "employees": 182000,
        "country": "United States",
        "website": "https://www.abc.xyz",
        "ceo": "Sundar Pichai",
        "founded": 1998,
        "competitors": ["MSFT", "AAPL", "META", "AMZN", "BIDU"],
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "ticker": "TSLA",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers",
        "exchange": "NASDAQ",
        "currency": "USD",
        "description": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, energy generation and storage systems.",
        "employees": 127855,
        "country": "United States",
        "website": "https://www.tesla.com",
        "ceo": "Elon Musk",
        "founded": 2003,
        "competitors": ["F", "GM", "RIVN", "NIO", "VWAGY"],
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "ticker": "AMZN",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail",
        "exchange": "NASDAQ",
        "currency": "USD",
        "description": "Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions, web services, and advertising globally.",
        "employees": 1541000,
        "country": "United States",
        "website": "https://www.amazon.com",
        "ceo": "Andy Jassy",
        "founded": 1994,
        "competitors": ["MSFT", "GOOGL", "ALIBABA", "WMT", "JD"],
    },
}

# ─── Financial Profiles (deterministic seed data) ────────────────────────────

_FINANCIALS = {
    "AAPL": {
        "current_price": 189.30,
        "market_cap": 2960000000000,
        "shares_outstanding": 15644000000,
        "annual": [
            # year, revenue, gross_profit, operating_income, net_income, eps, ebitda, fcf, total_debt, total_equity, current_assets, current_liabilities
            (2019, 260174, 98392, 63930, 55256, 2.97, 81860, 58896, 108047, 90488, 162819, 105718),
            (2020, 274515, 104956, 66288, 57411, 3.28, 82024, 73365, 112436, 65339, 143713, 105392),
            (2021, 365817, 152836, 108949, 94680, 5.61, 128362, 92953, 136522, 63090, 134836, 125481),
            (2022, 394328, 170782, 119437, 99803, 6.11, 135364, 111443, 120069, 50672, 135405, 153982),
            (2023, 383285, 169148, 114301, 96995, 6.13, 130101, 99584, 111088, 62146, 143566, 145308),
        ],
        "ratios": {"pe": 29.4, "pb": 46.1, "ev_ebitda": 23.7, "quick_ratio": 0.94},
        "price_history_seed": 145.0,
        "beta": 1.29,
    },
    "MSFT": {
        "current_price": 415.50,
        "market_cap": 3090000000000,
        "shares_outstanding": 7440000000,
        "annual": [
            (2019, 125843, 82933, 42959, 39240, 5.06, 55990, 38260, 78366, 102330, 175552, 60054),
            (2020, 143015, 96937, 52959, 44281, 5.76, 66985, 45234, 82271, 118304, 184406, 72310),
            (2021, 168088, 115856, 69916, 61271, 8.05, 85135, 56118, 74062, 141988, 211915, 88657),
            (2022, 198270, 135620, 83383, 72738, 9.65, 100239, 63326, 78395, 166542, 247024, 95082),
            (2023, 211915, 146052, 88523, 72361, 9.72, 105215, 59475, 79381, 206223, 247024, 104149),
        ],
        "ratios": {"pe": 36.4, "pb": 13.2, "ev_ebitda": 26.8, "quick_ratio": 1.78},
        "price_history_seed": 220.0,
        "beta": 0.92,
    },
    "GOOGL": {
        "current_price": 164.20,
        "market_cap": 2040000000000,
        "shares_outstanding": 12430000000,
        "annual": [
            (2019, 161857, 77270, 34231, 34343, 2.46, 44042, 30972, 4366, 201442, 152578, 39225),
            (2020, 182527, 97795, 41224, 40269, 2.93, 54140, 42843, 14312, 222544, 174296, 56834),
            (2021, 257637, 146698, 78714, 76033, 5.61, 91804, 67012, 14817, 251635, 188702, 64254),
            (2022, 282836, 156633, 74842, 59972, 4.56, 89937, 60010, 14701, 256144, 200406, 69300),
            (2023, 307394, 174062, 84293, 73795, 5.80, 97959, 68731, 13253, 283379, 198759, 81814),
        ],
        "ratios": {"pe": 26.3, "pb": 6.2, "ev_ebitda": 19.4, "quick_ratio": 2.10},
        "price_history_seed": 90.0,
        "beta": 1.06,
    },
    "TSLA": {
        "current_price": 248.50,
        "market_cap": 793000000000,
        "shares_outstanding": 3190000000,
        "annual": [
            (2019, 24578, 4069, -69, -862, -0.33, 2209, -1013, 13419, 6580, 12103, 10667),
            (2020, 31536, 6630, 1994, 721, 0.25, 4150, 2786, 12113, 22225, 26717, 19705),
            (2021, 53823, 13656, 6523, 5519, 1.87, 8820, 4585, 8873, 30189, 27100, 24683),
            (2022, 81462, 20853, 13656, 12556, 3.62, 17640, 7622, 5203, 44704, 32177, 26709),
            (2023, 96773, 17660, 8891, 14974, 4.30, 12478, 4358, 5498, 62634, 33050, 28708),
        ],
        "ratios": {"pe": 57.8, "pb": 14.2, "ev_ebitda": 46.2, "quick_ratio": 1.73},
        "price_history_seed": 180.0,
        "beta": 2.31,
    },
    "AMZN": {
        "current_price": 196.10,
        "market_cap": 2080000000000,
        "shares_outstanding": 10610000000,
        "annual": [
            (2019, 280522, 114986, 14541, 11588, 23.01, 36135, 25825, 84389, 62060, 96334, 87812),
            (2020, 386064, 152757, 22899, 21331, 41.83, 50408, 31021, 84389, 93404, 132733, 113091),
            (2021, 469822, 197478, 24879, 33364, 64.81, 58328, -9345, 116395, 138245, 161580, 142266),
            (2022, 513983, 225152, 12248, -2722, -0.27, 43898, -16068, 130381, 146043, 146791, 155393),
            (2023, 574785, 270534, 36852, 30425, 2.90, 85978, 35464, 135944, 201875, 180461, 164922),
        ],
        "ratios": {"pe": 45.2, "pb": 9.8, "ev_ebitda": 28.4, "quick_ratio": 0.84},
        "price_history_seed": 100.0,
        "beta": 1.18,
    },
}

# ─── News Headlines (demo) ────────────────────────────────────────────────────

_NEWS_TEMPLATES = {
    "AAPL": [
        ("Apple reports record iPhone 15 sales in emerging markets", "positive", "Earnings"),
        ("Apple Vision Pro launch drives developer interest in spatial computing", "positive", "Product Launch"),
        ("Apple faces EU antitrust investigation over App Store policies", "negative", "Regulation"),
        ("Apple expands AI capabilities with new on-device models", "positive", "Technology"),
        ("Supply chain disruptions may affect Q4 iPhone production", "negative", "Supply Chain"),
        ("Apple Services revenue grows 16% YoY, beating expectations", "positive", "Earnings"),
        ("Warren Buffett increases Berkshire's Apple stake to $170B", "positive", "Market"),
        ("Apple's India manufacturing push accelerates amid China tensions", "neutral", "Macroeconomics"),
        ("Apple Pay expands to 15 new countries", "positive", "Product Launch"),
        ("Analysts raise AAPL price target on strong margin outlook", "positive", "Market"),
        ("Apple settles patent dispute with Qualcomm for undisclosed sum", "neutral", "Legal"),
        ("iPhone market share declines in China as Huawei recovers", "negative", "Competition"),
    ],
    "MSFT": [
        ("Microsoft Azure cloud revenue grows 28% driven by AI demand", "positive", "Earnings"),
        ("Microsoft Copilot integration boosts Office 365 enterprise adoption", "positive", "Product Launch"),
        ("Microsoft acquires gaming studio to strengthen Xbox portfolio", "positive", "M&A"),
        ("EU regulators scrutinize Microsoft-Activision integration", "negative", "Regulation"),
        ("Microsoft AI investments reach $13B, expanding datacenter capacity", "positive", "Technology"),
        ("Microsoft reports strong Q3 earnings, raises full-year guidance", "positive", "Earnings"),
        ("Cybersecurity breach exposes Microsoft Exchange vulnerabilities", "negative", "Legal"),
        ("Microsoft Teams user base crosses 300 million monthly active users", "positive", "Market Demand"),
        ("Azure gains market share from AWS in enterprise segment", "positive", "Competition"),
        ("Microsoft commits $3.3B to AI infrastructure in Wisconsin", "positive", "Technology"),
    ],
    "GOOGL": [
        ("Google Search ad revenue rebounds strongly after AI integration", "positive", "Earnings"),
        ("Google Cloud emerges as third-largest provider with 28% growth", "positive", "Earnings"),
        ("DOJ antitrust trial poses long-term structural risk to Google Search", "negative", "Regulation"),
        ("Google Gemini AI outperforms GPT-4 on key benchmarks", "positive", "Technology"),
        ("YouTube Shorts monetization improves, closing gap with TikTok", "positive", "Market Demand"),
        ("Alphabet announces $70B buyback program, boosting investor confidence", "positive", "Market"),
        ("Google faces class action over privacy tracking in incognito mode", "negative", "Legal"),
        ("Waymo expands robotaxi service to three new US cities", "positive", "Product Launch"),
        ("Search market share slips slightly as Bing AI gains momentum", "negative", "Competition"),
        ("Google DeepMind achieves breakthrough in protein structure prediction", "positive", "Technology"),
    ],
    "TSLA": [
        ("Tesla Cybertruck deliveries ramp up with improved range figures", "positive", "Product Launch"),
        ("Tesla faces recall of 1.2M vehicles over autopilot software defect", "negative", "Legal"),
        ("Tesla cuts prices again in China amid intensifying BYD competition", "negative", "Competition"),
        ("Tesla FSD Version 12 shows marked improvement in urban driving", "positive", "Technology"),
        ("Elon Musk's political activities raise concerns among institutional investors", "negative", "Management"),
        ("Tesla energy storage deployments hit record 14.7 GWh in Q4", "positive", "Earnings"),
        ("Supercharger network opens to third-party vehicles, revenue opportunity grows", "positive", "Market Demand"),
        ("Tesla Gigafactory Mexico paused amid tariff uncertainty", "negative", "Macroeconomics"),
        ("Short sellers increase Tesla positions as growth slows", "negative", "Market"),
        ("Tesla Semi commercial deliveries expand to 50+ enterprise clients", "positive", "Product Launch"),
    ],
    "AMZN": [
        ("Amazon AWS revenue growth accelerates to 17% YoY in Q3", "positive", "Earnings"),
        ("Amazon Prime membership crosses 200 million globally", "positive", "Market Demand"),
        ("Amazon faces FTC antitrust lawsuit over marketplace practices", "negative", "Regulation"),
        ("Amazon Bedrock AI platform adoption grows 3x quarter-over-quarter", "positive", "Technology"),
        ("Amazon logistics network achieves same-day delivery in 90+ US cities", "positive", "Product Launch"),
        ("Amazon workers strike disrupts holiday season operations", "negative", "Supply Chain"),
        ("Amazon advertising revenue surpasses $12B quarterly, becoming third-largest ad platform", "positive", "Earnings"),
        ("Amazon Project Kuiper satellite launch marks entry into broadband market", "positive", "Product Launch"),
        ("Rising fulfillment costs pressure Amazon retail margins", "negative", "Earnings"),
        ("Amazon healthcare expansion accelerates with One Medical integration", "positive", "M&A"),
    ],
}


def get_price_history(ticker: str, periods: int = 60) -> List[Dict]:
    """Generate realistic stock price history using a seeded random walk."""
    seed_data = _FINANCIALS.get(ticker, {})
    base_price = seed_data.get("price_history_seed", 100.0)
    beta = seed_data.get("beta", 1.0)

    random.seed(hash(ticker) % 10000)
    prices = []
    price = base_price
    today = datetime.now()

    for i in range(periods, -1, -1):
        date = today - timedelta(days=i * 7)
        # Drift upward slightly with volatility proportional to beta
        drift = 0.002
        vol = 0.025 * beta
        change = random.gauss(drift, vol)
        price = price * (1 + change)
        price = max(price, 1.0)
        volume = int(random.uniform(40_000_000, 120_000_000))
        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(price * (1 - random.uniform(0, 0.01)), 2),
            "high": round(price * (1 + random.uniform(0, 0.02)), 2),
            "low": round(price * (1 - random.uniform(0, 0.02)), 2),
            "close": round(price, 2),
            "volume": volume,
        })

    # Override last close with current_price
    if prices:
        prices[-1]["close"] = seed_data.get("current_price", prices[-1]["close"])

    return prices


def get_company_info(ticker: str) -> Dict[str, Any]:
    """Return company metadata."""
    ticker = ticker.upper()
    if ticker not in DEMO_COMPANIES:
        return _unknown_company(ticker)
    info = DEMO_COMPANIES[ticker].copy()
    fin = _FINANCIALS.get(ticker, {})
    info["current_price"] = fin.get("current_price", 0)
    info["market_cap"] = fin.get("market_cap", 0)
    info["beta"] = fin.get("beta", 1.0)
    return info


def get_financials(ticker: str) -> Dict[str, Any]:
    """Return structured multi-year financial data."""
    ticker = ticker.upper()
    if ticker not in _FINANCIALS:
        return {}

    fin = _FINANCIALS[ticker]
    annual_data = []
    for row in fin["annual"]:
        yr, rev, gp, oi, ni, eps, ebitda, fcf, debt, equity, ca, cl = row
        annual_data.append({
            "year": yr,
            "revenue": rev * 1_000_000,
            "gross_profit": gp * 1_000_000,
            "operating_income": oi * 1_000_000,
            "net_income": ni * 1_000_000,
            "eps": eps,
            "ebitda": ebitda * 1_000_000,
            "free_cash_flow": fcf * 1_000_000,
            "total_debt": debt * 1_000_000,
            "total_equity": equity * 1_000_000,
            "current_assets": ca * 1_000_000,
            "current_liabilities": cl * 1_000_000,
        })

    return {
        "ticker": ticker,
        "currency": "USD",
        "annual": annual_data,
        "current_price": fin["current_price"],
        "market_cap": fin["market_cap"],
        "shares_outstanding": fin["shares_outstanding"],
        "ratios": fin["ratios"],
        "price_history": get_price_history(ticker),
    }


def get_news(ticker: str) -> List[Dict[str, Any]]:
    """Return simulated news headlines with sentiment labels."""
    ticker = ticker.upper()
    headlines = _NEWS_TEMPLATES.get(ticker, _generic_news())
    random.seed(hash(ticker + "news") % 10000)
    result = []
    today = datetime.now()
    for i, (headline, sentiment, topic) in enumerate(headlines):
        days_ago = random.randint(0, 30)
        result.append({
            "headline": headline,
            "sentiment": sentiment,
            "topic": topic,
            "source": random.choice(["Reuters", "Bloomberg", "CNBC", "WSJ", "Financial Times", "MarketWatch"]),
            "published_at": (today - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "url": "#",
        })
    result.sort(key=lambda x: x["published_at"], reverse=True)
    return result


def get_competitors(ticker: str) -> List[Dict[str, Any]]:
    """Return competitor financial snapshots for benchmarking."""
    ticker = ticker.upper()
    comp_tickers = DEMO_COMPANIES.get(ticker, {}).get("competitors", [])
    result = []
    for ct in comp_tickers[:5]:
        base = _FINANCIALS.get(ct)
        if base:
            ann = base["annual"]
            latest = ann[-1]
            prev = ann[-2]
            yr, rev, gp, oi, ni, eps, ebitda, fcf, debt, equity, ca, cl = latest
            _, prev_rev, _, _, _, prev_eps, _, _, _, _, _, _ = prev
            result.append({
                "ticker": ct,
                "name": DEMO_COMPANIES.get(ct, {}).get("name", ct),
                "market_cap": base["market_cap"],
                "current_price": base["current_price"],
                "revenue": rev * 1_000_000,
                "revenue_growth": round((rev / prev_rev - 1) * 100, 2),
                "net_income": ni * 1_000_000,
                "net_margin": round(ni / rev * 100, 2),
                "operating_income": oi * 1_000_000,
                "operating_margin": round(oi / rev * 100, 2),
                "eps": eps,
                "eps_growth": round((eps / prev_eps - 1) * 100, 2) if prev_eps != 0 else 0,
                "roe": round(ni / equity * 100, 2),
                "roa": round(ni / (equity + debt) * 100, 2),
                "debt_to_equity": round(debt / equity, 2) if equity else 0,
                "pe": base["ratios"].get("pe", 0),
                "pb": base["ratios"].get("pb", 0),
                "ebitda": ebitda * 1_000_000,
                "free_cash_flow": fcf * 1_000_000,
            })
        else:
            # Synthetic competitor data for tickers not in our universe
            result.append(_synthetic_competitor(ct))
    return result


def _unknown_company(ticker: str) -> Dict[str, Any]:
    return {
        "name": f"{ticker} Corporation",
        "ticker": ticker,
        "sector": "Unknown",
        "industry": "Unknown",
        "exchange": "Unknown",
        "currency": "USD",
        "description": "Company information not available in demo dataset.",
        "employees": 0,
        "country": "Unknown",
        "ceo": "Unknown",
        "founded": 0,
        "current_price": 0,
        "market_cap": 0,
        "beta": 1.0,
        "competitors": [],
    }


def _generic_news() -> List[tuple]:
    return [
        ("Company reports quarterly results in line with analyst expectations", "neutral", "Earnings"),
        ("Management announces strategic review of business segments", "neutral", "Management"),
        ("Analyst upgrades stock citing improving margin outlook", "positive", "Market"),
        ("Regulatory review of industry practices may impact operations", "negative", "Regulation"),
        ("Company expands into new geographic markets", "positive", "Market Demand"),
    ]


def _synthetic_competitor(ticker: str) -> Dict[str, Any]:
    random.seed(hash(ticker) % 9999)
    rev = random.uniform(50e9, 400e9)
    margin = random.uniform(0.08, 0.25)
    roe = random.uniform(0.10, 0.30)
    return {
        "ticker": ticker,
        "name": f"{ticker} Corp",
        "market_cap": int(random.uniform(200e9, 2000e9)),
        "current_price": round(random.uniform(50, 500), 2),
        "revenue": rev,
        "revenue_growth": round(random.uniform(-5, 25), 2),
        "net_income": rev * margin,
        "net_margin": round(margin * 100, 2),
        "operating_income": rev * (margin + 0.03),
        "operating_margin": round((margin + 0.03) * 100, 2),
        "eps": round(random.uniform(1, 15), 2),
        "eps_growth": round(random.uniform(-10, 30), 2),
        "roe": round(roe * 100, 2),
        "roa": round(roe * 0.6 * 100, 2),
        "debt_to_equity": round(random.uniform(0.1, 2.0), 2),
        "pe": round(random.uniform(15, 50), 1),
        "pb": round(random.uniform(2, 20), 1),
        "ebitda": rev * (margin + 0.05),
        "free_cash_flow": rev * margin * 0.7,
    }


def get_available_tickers() -> List[Dict[str, str]]:
    return [
        {"ticker": k, "name": v["name"], "sector": v["sector"]}
        for k, v in DEMO_COMPANIES.items()
    ]
