"""
InvestIQ — Sequential AI Investment Analyst
Flask Application Entry Point
"""

import os
import sys

# Ensure project root is on the path when running from investiq/
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, send_file
from backend.routes.api import api

# ── App factory ──────────────────────────────────────────────────────────────

def create_app() -> Flask:
    _base = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        static_folder=os.path.join(_base, "frontend", "static"),
        template_folder=os.path.join(_base, "frontend", "templates"),
    )

    # Load settings from environment
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "investiq-dev-secret-change-in-prod")
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Register API blueprint
    app.register_blueprint(api)

    # ── Frontend routes ───────────────────────────────────────────────────────

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_file(os.path.join(app.template_folder, "index.html"))

    # ── CORS headers (for development) ───────────────────────────────────────
    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.errorhandler(404)
    def not_found(e):
        from flask import jsonify
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"InvestIQ starting on http://localhost:{port}")
    print(f"   Mode: {'Development' if debug else 'Production'}")
    print(f"   Demo Mode: Active (no API keys required)")
    app.run(host="0.0.0.0", port=port, debug=debug)
