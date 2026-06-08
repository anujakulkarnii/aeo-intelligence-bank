"""
AEO Intelligence Bank — Flask Web App
Serves the intelligence bank UI and live bank.json data.
"""

import json
import os
from flask import Flask, jsonify, render_template, abort

app = Flask(__name__)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
BANK_PATH = os.path.join(BASE_DIR, "bank.json")

VALID_SECTIONS = {
    "icp_phrases", "fanout_terms", "citations", "competitor_complaints",
    "outbound_hooks", "hypotheses", "sales_calls", "next_queries",
    "ai_citations", "digests", "meta",
}


def load_bank() -> dict:
    try:
        with open(BANK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"meta": {}, "error": "bank.json not found — run the pipeline first."}
    except json.JSONDecodeError as e:
        return {"meta": {}, "error": f"bank.json parse error: {e}"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    return jsonify(load_bank())


@app.route("/api/section/<name>")
def api_section(name):
    if name not in VALID_SECTIONS:
        abort(404)
    bank = load_bank()
    return jsonify(bank.get(name, []))


@app.route("/api/meta")
def api_meta():
    return jsonify(load_bank().get("meta", {}))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
