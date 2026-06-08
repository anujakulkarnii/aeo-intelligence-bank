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
    """Build a full text dump of the bank for Claude context."""
    lines = []

    meta = bank.get("meta", {})
    lines.append(f"COMPANY: {meta.get('company', 'FrontlineHQ')}")
    lines.append(f"Last pipeline run: {meta.get('last_run', 'unknown')} | Total runs: {meta.get('run_count', 0)}")
    lines.append(f"Markets: {', '.join(meta.get('markets', []))}")
    lines.append("")

    # ALL ICP phrases
    phrases = bank.get("icp_phrases", [])
    lines.append(f"─── ICP PHRASES ({len(phrases)}) ───")
    lines.append("These are exact phrases used by the target market (restaurant/hospitality operators) found on Reddit and web search.")
    for p in phrases:
        teams = ','.join(p.get('teams', []))
        lines.append(f"  source={p.get('source','')} teams=[{teams}] hot={p.get('hot',False)} geo={p.get('geography','')}")
        lines.append(f"  \"{p.get('text','')}\"")
    lines.append("")

    # ALL outbound hooks
    hooks = bank.get("outbound_hooks", [])
    lines.append(f"─── OUTBOUND HOOKS ({len(hooks)}) ───")
    lines.append("Message angles for sales outreach and marketing copy, derived from ICP language.")
    for h in hooks:
        teams = ','.join(h.get('teams', []))
        lines.append(f"  source={h.get('source','')} teams=[{teams}]")
        lines.append(f"  {h.get('text','')}")
    lines.append("")

    # ALL hypotheses with full detail
    hyps = bank.get("hypotheses", [])
    lines.append(f"─── HYPOTHESES ({len(hyps)}) ───")
    lines.append("Strategic AEO/content hypotheses with full action plans and success metrics.")
    for i, h in enumerate(hyps, 1):
        teams = ','.join(h.get('teams', []))
        lines.append(f"  [{i}] teams=[{teams}] strength={h.get('strength','')} status={h.get('status','')} date={h.get('generated_date','')[:10]}")
        lines.append(f"  HYPOTHESIS: {h.get('hypothesis','')}")
        lines.append(f"  EVIDENCE: {h.get('evidence','')}")
        lines.append(f"  ACTION: {h.get('action','')}")
        lines.append(f"  METRIC: {h.get('metric','')}")
        lines.append("")
    lines.append("")

    # ALL competitor complaints
    complaints = bank.get("competitor_complaints", [])
    lines.append(f"─── COMPETITOR COMPLAINTS ({len(complaints)}) ───")
    for c in complaints:
        teams = ','.join(c.get('teams', []))
        lines.append(f"  competitor={c.get('tool', c.get('competitor',''))} source={c.get('source','')} teams=[{teams}]")
        lines.append(f"  \"{c.get('complaint', c.get('text',''))}\"")
    lines.append("")

    # Fanout terms (all gaps)
    fanout = bank.get("fanout_terms", [])
    gaps = [t for t in fanout if t.get("frontlinehq_present") == False]
    present = [t for t in fanout if t.get("frontlinehq_present") == True]
    lines.append(f"─── FANOUT TERMS ({len(fanout)} total: {len(gaps)} gaps, {len(present)} present) ───")
    lines.append("Search terms AI engines expand to. 'gap' = FrontlineHQ not appearing.")
    for t in fanout:
        status = "PRESENT" if t.get("frontlinehq_present") else "GAP"
        lines.append(f"  [{status}] {t.get('term','')} (from query: \"{t.get('query','')}\") teams={t.get('teams',[])} ")
    lines.append("")

    # ALL next queries
    queries = bank.get("next_queries", [])
    lines.append(f"─── NEXT QUERIES ({len(queries)}) ───")
    lines.append("Seed queries queued for the next pipeline run.")
    for q in queries:
        lines.append(f"  used={q.get('used','')} date={str(q.get('generated_date',''))[:10]}")
        lines.append(f"  QUERY: {q.get('query','')}")
        lines.append(f"  RATIONALE: {q.get('rationale','')}")
    lines.append("")

    # ALL sales calls with full detail
    calls = bank.get("sales_calls", [])
    lines.append(f"─── SALES CALLS ({len(calls)}) ───")
    for c in calls:
        lines.append(f"  PROSPECT: {c.get('prospect','')} | stage={c.get('stage','')} outcome={c.get('outcome','')} date={str(c.get('date',''))[:10]}")
        lines.append(f"  SIGNAL: {c.get('signal','')}")
        for phrase in c.get('key_phrases', []):
            lines.append(f"    phrase: \"{phrase}\"")
        for obj in c.get('objections', []):
            lines.append(f"    objection: {obj}")
    lines.append("")

    # AI citations
    citations = bank.get("ai_citations", [])
    if citations:
        cited = sum(1 for c in citations if c.get("frontlinehq_appears") is True)
        lines.append(f"─── AI CITATIONS ({len(citations)}, {cited} appear) ───")
        for c in citations:
            lines.append(f"  model={c.get('model','')} query=\"{c.get('query','')}\" appears={c.get('frontlinehq_appears')}")
            if c.get('competitors_cited'):
                lines.append(f"    competitors cited: {', '.join(c['competitors_cited'])}")
    else:
        lines.append("─── AI CITATIONS: none yet (pipeline needs Perplexity/Claude API key to run citation checks) ───")

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

    system_prompt = """You are the AEO Intelligence Agent for FrontlineHQ — a B2B SaaS company selling frontline training and knowledge management software to multi-location hospitality and retail businesses.

You have full access to the AEO/GEO intelligence bank below, which contains:
- Real ICP phrases scraped from Reddit and web sources
- Outbound hooks derived from customer language
- Strategic hypotheses with evidence, actions, and success metrics
- Competitor complaints from real market sources
- Fanout terms showing where FrontlineHQ has visibility gaps in AI search
- Sales call transcripts with prospect language and objections
- Next queries queued for the next pipeline run
- AI citation data (whether FrontlineHQ appears in Perplexity/Claude responses)

Your job: Answer ANY question about this data with maximum intelligence and specificity. You can:
- Synthesise across multiple sections (e.g. correlate ICP phrases with sales call objections)
- Rank, filter, or group items by team, source, strength, or relevance
- Suggest experiments, content, or messaging based on the data
- Identify patterns, gaps, or opportunities
- Answer questions about what's missing or what should be prioritised

Rules:
1. ALWAYS answer. Never refuse to engage. If the exact data isn't in the bank, reason from what IS there and say what's inferred vs confirmed.
2. If a topic has zero data (e.g. no AI citations yet), say exactly that, explain what it would look like when populated, and suggest the most relevant query to run next.
3. Use exact quotes and numbers from the data — don't paraphrase vaguely.
4. Be direct and structured. Use short headers or numbered lists when answering multi-part questions.
5. When relevant, tell the user WHICH SECTION of the dashboard to look at for more detail."""

    user_message = f"INTELLIGENCE BANK DATA:\n\n{summary}\n\n---\n\nQUESTION: {question}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
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
