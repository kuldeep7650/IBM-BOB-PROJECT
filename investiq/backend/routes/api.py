"""
InvestIQ REST API Routes
"""

import uuid
import threading
import time
from typing import Dict, Any

from flask import Blueprint, jsonify, request, Response
from backend.orchestrator import InvestmentAnalysisOrchestrator
from backend.providers.demo_data import get_available_tickers, get_company_info
from backend.services.report_generator import generate_html_report

api = Blueprint("api", __name__, url_prefix="/api")

# In-memory analysis store (replace with DB for production)
_analyses: Dict[str, Any] = {}
_progress: Dict[str, list] = {}


# ── Health ────────────────────────────────────────────────────────────────────

@api.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "InvestIQ API", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})


# ── Companies ─────────────────────────────────────────────────────────────────

@api.route("/companies", methods=["GET"])
def list_companies():
    return jsonify({"companies": get_available_tickers(), "is_demo": True})


@api.route("/company/<ticker>", methods=["GET"])
def get_company(ticker: str):
    info = get_company_info(ticker.upper())
    return jsonify(info)


@api.route("/company/<ticker>/financials", methods=["GET"])
def get_company_financials(ticker: str):
    from backend.providers.demo_data import get_financials
    data = get_financials(ticker.upper())
    if not data:
        return jsonify({"error": f"No financial data for {ticker}"}), 404
    return jsonify(data)


@api.route("/company/<ticker>/news", methods=["GET"])
def get_company_news(ticker: str):
    from backend.providers.demo_data import get_news
    news = get_news(ticker.upper())
    return jsonify({"news": news, "count": len(news)})


@api.route("/company/<ticker>/competitors", methods=["GET"])
def get_company_competitors(ticker: str):
    from backend.providers.demo_data import get_competitors
    comps = get_competitors(ticker.upper())
    return jsonify({"competitors": comps, "count": len(comps)})


# ── Analysis ──────────────────────────────────────────────────────────────────

@api.route("/analysis/run", methods=["POST"])
def run_analysis():
    """Start a sequential analysis and return analysis_id immediately."""
    body = request.get_json(force=True, silent=True) or {}
    ticker = (body.get("ticker") or "").strip().upper()
    period = body.get("period", "5y")

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400
    if len(ticker) > 10 or not ticker.isalpha():
        return jsonify({"error": "Invalid ticker format"}), 400

    analysis_id = str(uuid.uuid4())
    _analyses[analysis_id] = {"status": "running", "ticker": ticker}
    _progress[analysis_id] = []

    def _run():
        try:
            orch = InvestmentAnalysisOrchestrator()

            def on_progress(stage_id, status, message):
                _progress[analysis_id].append({
                    "stage_id": stage_id,
                    "status": status,
                    "message": message,
                    "ts": time.time(),
                })

            result = orch.run(ticker, period=period, progress_callback=on_progress)
            _analyses[analysis_id] = result
            _analyses[analysis_id]["status"] = result.get("status", "completed")
        except Exception as exc:
            _analyses[analysis_id] = {
                "status": "failed",
                "error": str(exc),
                "ticker": ticker,
                "id": analysis_id,
            }

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"analysis_id": analysis_id, "status": "running", "ticker": ticker}), 202


@api.route("/analysis/<analysis_id>", methods=["GET"])
def get_analysis(analysis_id: str):
    if analysis_id not in _analyses:
        return jsonify({"error": "Analysis not found"}), 404
    return jsonify(_analyses[analysis_id])


@api.route("/analysis/<analysis_id>/progress", methods=["GET"])
def get_progress(analysis_id: str):
    if analysis_id not in _analyses:
        return jsonify({"error": "Analysis not found"}), 404

    progress = _progress.get(analysis_id, [])
    status = _analyses[analysis_id].get("status", "running")
    return jsonify({"status": status, "progress": progress})


@api.route("/analysis/<analysis_id>/report", methods=["GET"])
def get_report(analysis_id: str):
    if analysis_id not in _analyses:
        return jsonify({"error": "Analysis not found"}), 404
    analysis = _analyses[analysis_id]
    if analysis.get("status") == "running":
        return jsonify({"error": "Analysis still running"}), 409

    fmt = request.args.get("format", "html")
    if fmt == "html":
        html = generate_html_report(analysis)
        return Response(html, mimetype="text/html",
                        headers={"Content-Disposition":
                                 f"attachment; filename=InvestIQ_{analysis.get('ticker','report')}_{analysis.get('timestamp','')[:10]}.html"})

    return jsonify({"error": "Unsupported format"}), 400
