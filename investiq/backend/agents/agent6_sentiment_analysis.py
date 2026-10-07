"""
Agent 6: Market Sentiment Analysis Agent
Analyzes news sentiment, scores overall market mood and identifies major topics.
"""

import time
from typing import Dict, Any, List

TOPIC_KEYWORDS = {
    "Earnings":      ["earnings", "revenue", "profit", "margin", "EPS", "guidance", "results"],
    "Product Launch": ["launch", "product", "feature", "announce", "release", "new"],
    "Regulation":    ["regulatory", "regulation", "FTC", "EU", "SEC", "antitrust", "DOJ", "compliance"],
    "Management":    ["CEO", "CFO", "executive", "leadership", "management", "board", "resign"],
    "M&A":           ["acqui", "merger", "deal", "buyout", "takeover", "stake", "purchase"],
    "Competition":   ["competitor", "market share", "rival", "compete", "beat", "outperform"],
    "Macroeconomics":["macro", "inflation", "interest rate", "GDP", "recession", "tariff", "trade"],
    "Legal":         ["lawsuit", "litigation", "settlement", "legal", "court", "class action", "patent"],
    "Supply Chain":  ["supply", "chain", "manufacturing", "production", "factory", "shortage", "disruption"],
    "Market Demand": ["demand", "adoption", "customer", "subscriber", "user", "growth", "expansion"],
    "Technology":    ["AI", "cloud", "software", "platform", "technology", "digital", "data"],
    "Market":        ["investor", "analyst", "target", "upgrade", "downgrade", "rating", "buyback"],
}

SENTIMENT_SCORES = {"positive": 1, "neutral": 0, "negative": -1}


def _classify_topics(headline: str) -> List[str]:
    hl_lower = headline.lower()
    found = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.lower() in hl_lower for kw in keywords):
            found.append(topic)
    return found or ["General"]


def run(competitor_data: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    data = competitor_data.get("output", {})
    news = data.get("news", [])
    ticker = data.get("ticker", "")

    if not news:
        return {
            "agent": "MarketSentimentAgent",
            "status": "completed",
            "execution_time": round(time.time() - start, 3),
            "warnings": ["No news data available for sentiment analysis."],
            "output": {**data, "sentiment": _empty_sentiment()},
            "summary": "No news data. Sentiment score: 0 (Neutral).",
        }

    total = len(news)
    pos = sum(1 for n in news if n.get("sentiment") == "positive")
    neg = sum(1 for n in news if n.get("sentiment") == "negative")
    neu = total - pos - neg

    # Weighted sentiment score: -100 to +100
    raw_score = sum(SENTIMENT_SCORES.get(n.get("sentiment", "neutral"), 0) for n in news)
    sentiment_score = round(raw_score / total * 100) if total else 0

    if sentiment_score >= 40:
        label = "Very Positive"
    elif sentiment_score >= 10:
        label = "Positive"
    elif sentiment_score >= -10:
        label = "Neutral"
    elif sentiment_score >= -40:
        label = "Negative"
    else:
        label = "Very Negative"

    # Enrich news with auto-detected topics
    enriched_news = []
    for item in news:
        topics = item.get("topic") or _classify_topics(item.get("headline", ""))
        if isinstance(topics, str):
            topics = [topics]
        enriched_news.append({**item, "topics": topics})

    # Aggregate topic frequencies
    topic_freq: Dict[str, int] = {}
    for item in enriched_news:
        for t in item.get("topics", []):
            topic_freq[t] = topic_freq.get(t, 0) + 1

    top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:6]

    # Positive/negative breakdown by topic
    topic_sentiment: Dict[str, Dict[str, int]] = {}
    for item in enriched_news:
        s = item.get("sentiment", "neutral")
        for t in item.get("topics", []):
            if t not in topic_sentiment:
                topic_sentiment[t] = {"positive": 0, "neutral": 0, "negative": 0}
            topic_sentiment[t][s] = topic_sentiment[t].get(s, 0) + 1

    sentiment_result = {
        "score": sentiment_score,
        "label": label,
        "total_articles": total,
        "positive_count": pos,
        "neutral_count": neu,
        "negative_count": neg,
        "positive_pct": round(pos / total * 100, 1) if total else 0,
        "negative_pct": round(neg / total * 100, 1) if total else 0,
        "neutral_pct": round(neu / total * 100, 1) if total else 0,
        "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
        "topic_sentiment": topic_sentiment,
        "recent_headlines": enriched_news[:8],
    }

    out = data.copy()
    out["sentiment"] = sentiment_result

    return {
        "agent": "MarketSentimentAgent",
        "status": "completed",
        "execution_time": round(time.time() - start, 3),
        "warnings": [],
        "output": out,
        "summary": (
            f"Sentiment score: {sentiment_score} ({label}). "
            f"{pos} positive / {neu} neutral / {neg} negative articles. "
            f"Top topic: {top_topics[0][0] if top_topics else 'N/A'}."
        ),
    }


def _empty_sentiment():
    return {
        "score": 0, "label": "Neutral", "total_articles": 0,
        "positive_count": 0, "neutral_count": 0, "negative_count": 0,
        "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0,
        "top_topics": [], "topic_sentiment": {}, "recent_headlines": [],
    }
