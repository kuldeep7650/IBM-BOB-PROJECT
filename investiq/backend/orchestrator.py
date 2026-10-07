"""
InvestIQ Investment Analysis Orchestrator
Executes the sequential 9-stage investment analysis pipeline.

Pipeline:
  gatherData → validateData → extractKPIs → analyzeRatios → benchmarkCompetitors
  → analyzeSentiment → detectRisks → analyzeTrends → generateRecommendation
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Callable

from backend.providers import build_providers
from backend.agents import (
    agent1_data_gathering,
    agent2_data_validation,
    agent3_kpi_extraction,
    agent4_ratio_analysis,
    agent5_competitor_benchmarking,
    agent6_sentiment_analysis,
    agent7_risk_detection,
    agent8_trend_analysis,
    agent9_recommendation,
)

AGENT_STAGES = [
    ("data_gathering",          "Data Gathering",           agent1_data_gathering),
    ("data_validation",         "Data Validation",          agent2_data_validation),
    ("kpi_extraction",          "KPI Extraction",           agent3_kpi_extraction),
    ("ratio_analysis",          "Financial Ratio Analysis", agent4_ratio_analysis),
    ("competitor_benchmarking", "Competitor Benchmarking",  agent5_competitor_benchmarking),
    ("sentiment_analysis",      "Market Sentiment",         agent6_sentiment_analysis),
    ("risk_detection",          "Risk Detection",           agent7_risk_detection),
    ("trend_analysis",          "Trend & Forecast",         agent8_trend_analysis),
    ("recommendation",          "Investment Recommendation",agent9_recommendation),
]


class InvestmentAnalysisOrchestrator:
    """Runs the full sequential investment analysis pipeline."""

    def __init__(self):
        self.providers = build_providers()

    def run(
        self,
        ticker: str,
        period: str = "5y",
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full pipeline.

        Args:
            ticker: Stock ticker symbol
            period: Analysis period
            progress_callback: Optional callable(stage_id, status, message)

        Returns:
            Full structured analysis result
        """
        analysis_id = str(uuid.uuid4())
        pipeline_start = time.time()

        trace: List[Dict] = []
        current_output = None
        overall_status = "completed"

        def emit(stage_id: str, status: str, msg: str = ""):
            if progress_callback:
                progress_callback(stage_id, status, msg)

        for stage_id, stage_name, module in AGENT_STAGES:
            emit(stage_id, "running", f"Executing {stage_name}...")
            stage_start = time.time()

            try:
                if stage_id == "data_gathering":
                    result = module.run(ticker, self.providers, period)
                else:
                    result = module.run(current_output)

                current_output = result
                stage_time = round(time.time() - stage_start, 3)

                trace.append({
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "agent": result.get("agent", stage_name),
                    "status": "completed",
                    "execution_time": stage_time,
                    "summary": result.get("summary", ""),
                    "warnings": result.get("warnings", []),
                })

                emit(stage_id, "completed", result.get("summary", ""))

            except Exception as exc:
                stage_time = round(time.time() - stage_start, 3)
                error_msg = str(exc)
                overall_status = "partial"

                trace.append({
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "agent": stage_name,
                    "status": "failed",
                    "execution_time": stage_time,
                    "error": error_msg,
                    "warnings": [],
                })

                emit(stage_id, "failed", error_msg)
                # Continue pipeline with whatever data we have
                if current_output is None:
                    current_output = {"agent": stage_name, "status": "failed",
                                      "output": {}, "warnings": [error_msg]}

        total_time = round(time.time() - pipeline_start, 3)
        final_data = current_output.get("output", {}) if current_output else {}

        # Build top-level summary object
        result_payload = _build_result(
            analysis_id=analysis_id,
            ticker=ticker,
            final_data=final_data,
            trace=trace,
            total_time=total_time,
            overall_status=overall_status,
            is_demo=self.providers.get("is_demo", True),
        )

        return result_payload


def _build_result(
    analysis_id: str,
    ticker: str,
    final_data: Dict,
    trace: List[Dict],
    total_time: float,
    overall_status: str,
    is_demo: bool,
) -> Dict[str, Any]:
    """Build the structured final result payload."""
    rec = final_data.get("recommendation", {})
    risk = final_data.get("risk", {})
    sentiment = final_data.get("sentiment", {})
    forecast = final_data.get("forecast", {})
    kpis = final_data.get("kpis", {})
    company = final_data.get("company", {})
    fin = final_data.get("financials", {})

    def kv(key):
        return kpis.get(key, {}).get("value")

    return {
        "id": analysis_id,
        "ticker": ticker,
        "status": overall_status,
        "is_demo": is_demo,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_execution_time": total_time,

        # Company
        "company": company,
        "current_price": fin.get("current_price"),
        "market_cap": fin.get("market_cap"),

        # Validation
        "data_quality": final_data.get("validation", {}).get("score"),
        "data_quality_label": final_data.get("validation", {}).get("label"),
        "validation_issues": final_data.get("validation", {}).get("issues", []),

        # KPIs
        "kpis": kpis,
        "kpi_history": final_data.get("kpi_history", {}),
        "annual_history": final_data.get("annual_history", []),
        "price_history": fin.get("price_history", []),

        # Ratios
        "ratios": final_data.get("ratios", {}),

        # Competitors
        "competitor_analysis": final_data.get("competitor_analysis", {}),

        # Sentiment
        "sentiment": sentiment,

        # Risk
        "risk": risk,

        # Forecast
        "forecast": forecast,

        # Recommendation
        "recommendation": rec,

        # Trace
        "agent_trace": trace,

        # Quick-access summary
        "summary": {
            "ticker": ticker,
            "name": company.get("name", ticker),
            "action": rec.get("action", "N/A"),
            "score": rec.get("score"),
            "confidence": rec.get("confidence"),
            "risk_level": risk.get("level"),
            "risk_score": risk.get("score"),
            "sentiment_label": sentiment.get("label"),
            "sentiment_score": sentiment.get("score"),
            "outlook": forecast.get("outlook"),
            "data_quality": final_data.get("validation", {}).get("score"),
            "revenue": kv("revenue"),
            "net_margin": kv("net_margin"),
            "roe": kv("roe"),
            "pe": kv("pe"),
            "eps": kv("eps"),
        },
    }
