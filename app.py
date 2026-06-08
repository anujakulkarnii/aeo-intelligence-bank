"""
AEO Intelligence Bank — Flask Web App
Serves the React frontend and live bank.json API.
"""

import json
import os
import anthropic
from flask import Flask, jsonify, abort, send_from_directory, request

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BANK_PATH   = os.path.join(BASE_DIR, "bank.json")
REACT_BUILD = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(__name__, static_folder=None)

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


def build_bank_summary(bank: dict) -> str:
    """Build a concise text summary of the bank for Claude context."""
    lines = []

    meta = bank.get("meta", {})
    lines.append(f"Company: {meta.get('company', 'FrontlineHQ')}")
    lines.append(f"Last run: {meta.get('last_run', 'unknown')} | Run count: {meta.get('run_count', 0)}")
    lines.append("")

    phrases = bank.get("icp_phrases", [])
    if phrases:
        lines.append(f"ICP PHRASES ({len(phrases)} total):")
        for p in phrases[:20]:
            lines.append(f"  [{p.get('source','')} / {','.join(p.get('teams',[]))}] \"{p.get('text','')}\"")
        lines.append("")

    hooks = bank.get("outbound_hooks", [])
    if hooks:
        lines.append(f"OUTBOUND HOOKS ({len(hooks)} total):")
        for h in hooks[:15]:
            lines.append(f"  [{h.get('source','')} / {','.join(h.get('teams',[]))}] {h.get('text','')}")
        lines.append("")

    hyps = bank.get("hypotheses", [])
    if hyps:
        lines.append(f"HYPOTHESES ({len(hyps)} total):")
        for h in hyps:
            lines.append(f"  [{','.join(h.get('teams',[]))} / {h.get('strength','')}] {h.get('hypothesis','')}")
            if h.get("action"):
                lines.append(f"    Action: {h['action'][:200]}")
            if h.get("metric"):
                lines.append(f"    Metric: {h['metric'][:150]}")
        lines.append("")

    complaints = bank.get("competitor_complaints", [])
    if complaints:
        lines.append(f"COMPETITOR COMPLAINTS ({len(complaints)} total):")
        for c in complaints:
            lines.append(f"  [{c.get('tool','')} / {c.get('source','')}] {c.get('complaint','')}")
        lines.append("")

    fanout = bank.get("fanout_terms", [])
    if fanout:
        lines.append(f"FANOUT TERMS ({len(fanout)} total — gaps where FrontlineHQ is absent):")
        gaps = [t for t in fanout if t.get("frontlinehq_present") == False]
        for t in gaps[:15]:
            lines.append(f"  {t.get('term','')}")
        lines.append("")

    queries = bank.get("next_queries", [])
    if queries:
        lines.append(f"NEXT QUERIES ({len(queries)} queued):")
        for q in queries:
            lines.append(f"  {q.get('query','')} — {q.get('rationale','')[:120]}")
        lines.append("")

    calls = bank.get("sales_calls", [])
    if calls:
        lines.append(f"SALES CALLS ({len(calls)} total):")
        for c in calls:
            lines.append(f"  [{c.get('prospect','')} / {c.get('stage','')} / {c.get('outcome','')}]")
            lines.append(f"    Signal: {c.get('signal','')}")
            phrases_list = c.get("key_phrases", [])
            if phrases_list:
                lines.append(f"    Phrases: {' | '.join(phrases_list[:4])}")
        lines.append("")

    citations = bank.get("ai_citations", [])
    if citations:
        cited = sum(1 for c in citations if c.get("frontlinehq_appears") is True)
        lines.append(f"AI CITATIONS: {cited}/{len(citations)} queries where FrontlineHQ appears")

    return "\n".join(lines)


@app.route("/api/data")
def api_data():
    return jsonify(load_bank())


@app.route("/api/section/<name>")
def api_section(name):
    if name not in VALID_SECTIONS:
        abort(404)
    return jsonify(load_bank().get(name, []))


@app.route("/api/meta")
def api_meta():
    return jsonify(load_bank().get("meta", {}))


@app.route("/api/ask", methods=["POST"])
def api_ask():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

    bank = load_bank()
    summary = build_bank_summary(bank)

    system_prompt = (
        "You are an AEO intelligence assistant for FrontlineHQ. "
        "You have access to the company's AEO/GEO intelligence bank — real data from Reddit, review sites, sales calls, and AI engine citation checks. "
        "Answer the user's question using the data provided. Be concise, direct, and specific. "
        "Reference exact phrases, competitor names, or hypothesis text when relevant. "
        "If the data doesn't contain enough to answer, say so clearly."
    )

    user_message = f"Here is the current intelligence bank:\n\n{summary}\n\n---\n\nQuestion: {question}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        answer = response.content[0].text
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    full = os.path.join(REACT_BUILD, path)
    if path and os.path.exists(full):
        return send_from_directory(REACT_BUILD, path)
    return send_from_directory(REACT_BUILD, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
