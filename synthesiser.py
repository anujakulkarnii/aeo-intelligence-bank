"""
AEO Intelligence System — Synthesiser
Generates the AEO digest as a clean HTML email and next-run query suggestions.

Claude returns structured JSON; Python builds the final HTML so layout
is pixel-perfect and renders cleanly in Gmail.
"""

import json
import textwrap
from typing import Optional
import anthropic

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    SYNTHESIS_SYSTEM_PROMPT,
    NEXT_QUERY_SYSTEM_PROMPT,
    TARGET_MARKETS,
)


# ── Claude helper ─────────────────────────────────────────────────────────────

def _call_claude(system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _parse_json(raw: str) -> Optional[dict]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[synthesiser] JSON parse error: {e}\nRaw: {raw[:300]}")
        return None


# ── HTML building blocks ──────────────────────────────────────────────────────

C_BG       = "#ffffff"
C_BG_ALT   = "#F8F7F4"
C_BORDER   = "#E8E5DF"
C_TEXT     = "#1a1a1a"
C_MUTED    = "#666666"
C_TEAL     = "#4A7C74"
C_HDR_BG   = "#1a1a1a"
C_HDR_FG   = "#ffffff"

CELL_STYLE = f"padding:10px 12px;border:1px solid {C_BORDER};font-size:13px;color:{C_TEXT};vertical-align:top;line-height:1.5;"
TH_STYLE   = f"background:{C_HDR_BG};color:{C_HDR_FG};font-size:11px;text-transform:uppercase;letter-spacing:1px;padding:10px 12px;border:1px solid {C_BORDER};text-align:left;"


def _section_header(title: str) -> str:
    return (
        f'<tr><td style="padding:28px 0 10px 0;">'
        f'<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;'
        f'color:{C_TEAL};font-family:Arial,sans-serif;font-weight:bold;">{title}</div>'
        f'<div style="border-bottom:1px solid {C_BORDER};margin-top:6px;"></div>'
        f'</td></tr>'
    )


def _html_table(headers: list, rows: list) -> str:
    """Build a full-width HTML table with alternating row colours."""
    ths = "".join(f'<th style="{TH_STYLE}">{h}</th>' for h in headers)
    body_rows = []
    for i, row in enumerate(rows):
        bg = C_BG if i % 2 == 0 else C_BG_ALT
        tds = "".join(
            f'<td style="{CELL_STYLE}background:{bg};">{v}</td>'
            for v in row
        )
        body_rows.append(f'<tr>{tds}</tr>')

    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;width:100%;margin-top:12px;">'
        f'<thead><tr>{ths}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        f'</table>'
    )


def _hook_block(text: str, n: int) -> str:
    return (
        f'<div style="border-left:3px solid {C_TEAL};padding:10px 14px;'
        f'background:{C_BG_ALT};margin:10px 0;font-size:13px;'
        f'color:{C_TEXT};line-height:1.6;font-family:Arial,sans-serif;">'
        f'<strong style="color:{C_TEAL};">{n}.</strong> &ldquo;{text}&rdquo;'
        f'</div>'
    )


def _kv_row(key: str, value: str) -> str:
    return (
        f'<tr>'
        f'<td style="padding:6px 12px 6px 0;font-size:11px;text-transform:uppercase;'
        f'letter-spacing:1px;color:{C_MUTED};white-space:nowrap;vertical-align:top;'
        f'font-family:Arial,sans-serif;width:100px;">{key}</td>'
        f'<td style="padding:6px 0;font-size:13px;color:{C_TEXT};vertical-align:top;'
        f'line-height:1.5;font-family:Arial,sans-serif;">{value}</td>'
        f'</tr>'
    )


def _phrase_pill(text: str) -> str:
    return (
        f'<div style="padding:8px 0;border-bottom:1px solid {C_BORDER};'
        f'font-size:13px;color:{C_TEXT};font-family:Arial,sans-serif;line-height:1.5;">'
        f'&ldquo;{text}&rdquo;</div>'
    )


# ── Full email builder ────────────────────────────────────────────────────────

def _build_html_email(
    synthesis:      dict,
    next_queries:   list,
    citations:      list,
    ai_citations:   list,
    run_date:       str,
    active_queries: list,
) -> str:
    date_str = run_date[:10]
    markets  = " &middot; ".join(m["name"] for m in TARGET_MARKETS)

    # Google (Tavily) citation counts per market
    us_hits  = sum(1 for c in citations if c.get("market") == "US" and c.get("frontlinehq_appears"))
    us_total = sum(1 for c in citations if c.get("market") == "US")
    uk_hits  = sum(1 for c in citations if c.get("market") == "UK" and c.get("frontlinehq_appears"))
    uk_total = sum(1 for c in citations if c.get("market") == "UK")

    # AI engine citation counts
    perp_hits  = sum(1 for r in ai_citations if r.get("model") == "perplexity-sonar" and r.get("frontlinehq_appears"))
    perp_total = sum(1 for r in ai_citations if r.get("model") == "perplexity-sonar")
    cl_hits    = sum(1 for r in ai_citations if r.get("model") == "claude-web" and r.get("frontlinehq_appears"))
    cl_total   = sum(1 for r in ai_citations if r.get("model") == "claude-web")

    body_parts = []

    # ── 1. Header ─────────────────────────────────────────────────────────────
    body_parts.append(
        f'<tr><td style="padding:32px 0 24px 0;border-bottom:2px solid {C_TEXT};">'
        f'<div style="font-size:11px;letter-spacing:3px;text-transform:uppercase;'
        f'color:{C_TEAL};font-family:Arial,sans-serif;font-weight:bold;">AEO PULSE</div>'
        f'<div style="font-size:24px;font-weight:bold;color:{C_TEXT};'
        f'font-family:Arial,sans-serif;margin:6px 0 4px 0;">FrontlineHQ</div>'
        f'<div style="font-size:13px;color:{C_MUTED};font-family:Arial,sans-serif;">'
        f'{date_str} &nbsp;&middot;&nbsp; Markets: {markets}</div>'
        f'</td></tr>'
    )

    # ── 2. Citation Rate ──────────────────────────────────────────────────────
    # Rows: one per engine (Google US, Google UK if present, Perplexity, Claude)
    cite_rows = []

    # Google rows
    cite_rows.append([
        "Google (Tavily) — US",
        f"{us_hits} of {us_total}",
        f"{int(us_hits / us_total * 100) if us_total else 0}%",
    ])
    if uk_total:
        cite_rows.append([
            "Google (Tavily) — UK",
            f"{uk_hits} of {uk_total}",
            f"{int(uk_hits / uk_total * 100) if uk_total else 0}%",
        ])

    # Perplexity row
    if perp_total:
        cite_rows.append([
            "Perplexity (sonar)",
            f"{perp_hits} of {perp_total}",
            f"{int(perp_hits / perp_total * 100)}%",
        ])
    else:
        cite_rows.append(["Perplexity (sonar)", "— no API key", "—"])

    # Claude row
    if cl_total:
        cite_rows.append([
            "Claude (web search)",
            f"{cl_hits} of {cl_total}",
            f"{int(cl_hits / cl_total * 100)}%",
        ])
    else:
        cite_rows.append(["Claude (web search)", "— not run", "—"])

    body_parts.append(_section_header("Citation Rate"))
    body_parts.append(
        f'<tr><td>'
        + _html_table(["Engine", "Queries Hit", "Rate"], cite_rows)
        + '</td></tr>'
    )

    # ── 3. Top 3 Content Gaps ─────────────────────────────────────────────────
    gaps = synthesis.get("content_gaps", [])[:3]
    gap_rows = [
        [str(i + 1), g.get("gap", ""), g.get("why_losing", ""),
         g.get("action", ""), g.get("timeline", "")]
        for i, g in enumerate(gaps)
    ]
    body_parts.append(_section_header("Top 3 Content Gaps"))
    body_parts.append(
        f'<tr><td>'
        + _html_table(["#", "Gap", "Why You're Losing", "Action This Week", "Timeline"], gap_rows)
        + '</td></tr>'
    )

    # ── 4. Outbound Hooks ─────────────────────────────────────────────────────
    hooks = synthesis.get("outbound_hooks", [])[:2]
    hook_html = "".join(_hook_block(h, i + 1) for i, h in enumerate(hooks)) \
                or f'<p style="color:{C_MUTED};font-size:13px;">None extracted this run.</p>'

    body_parts.append(_section_header("2 Outbound Hooks — Use This Week"))
    body_parts.append(f'<tr><td>{hook_html}</td></tr>')

    # ── 5. Top Hypothesis ─────────────────────────────────────────────────────
    hyp = synthesis.get("top_hypothesis", {})
    if hyp:
        strength_colour = {"strong": "#2D7A4F", "medium": "#B8860B", "weak": "#999"}.get(
            hyp.get("strength", "weak").lower(), "#999"
        )
        strength_label = (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
            f'background:{strength_colour};color:white;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:1px;">'
            f'{hyp.get("strength","").capitalize()}</span>'
        )
        kv_rows = (
            _kv_row("Hypothesis", hyp.get("hypothesis", "")) +
            _kv_row("Action", hyp.get("action", "")) +
            _kv_row("Metric", hyp.get("metric", "")) +
            _kv_row("Strength", strength_label) +
            _kv_row("Timeline", hyp.get("timeline", ""))
        )
        hyp_html = (
            f'<table cellpadding="0" cellspacing="0" style="width:100%;margin-top:12px;">'
            f'{kv_rows}</table>'
        )
    else:
        hyp_html = f'<p style="color:{C_MUTED};font-size:13px;">None generated.</p>'

    body_parts.append(_section_header("Top Hypothesis"))
    body_parts.append(f'<tr><td>{hyp_html}</td></tr>')

    # ── 6. New ICP Language ───────────────────────────────────────────────────
    phrases = synthesis.get("icp_phrases_highlight", [])[:6]
    phrase_html = "".join(_phrase_pill(p) for p in phrases) \
                  or f'<p style="color:{C_MUTED};font-size:13px;">None extracted this run.</p>'

    body_parts.append(_section_header("New ICP Language This Run"))
    body_parts.append(f'<tr><td style="padding-top:8px;">{phrase_html}</td></tr>')

    # ── 7. Competitor Alert ───────────────────────────────────────────────────
    alert = synthesis.get("competitor_alert")
    if alert and str(alert).lower() not in ("null", "none", ""):
        body_parts.append(_section_header("Competitor Alert"))
        body_parts.append(
            f'<tr><td style="font-size:13px;color:{C_TEXT};line-height:1.6;'
            f'font-family:Arial,sans-serif;padding-top:8px;">{alert}</td></tr>'
        )

    # ── 8. Queries to Test Next Run ───────────────────────────────────────────
    if next_queries:
        nq_rows = [
            [str(i + 1), nq.get("query", ""), nq.get("rationale", "")]
            for i, nq in enumerate(next_queries[:5])
        ]
        body_parts.append(_section_header("Queries to Test Next Run"))
        body_parts.append(
            f'<tr><td>'
            + _html_table(["#", "Query", "Why"], nq_rows)
            + '</td></tr>'
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    body_parts.append(
        f'<tr><td style="padding:32px 0 16px 0;border-top:1px solid {C_BORDER};'
        f'margin-top:24px;text-align:center;">'
        f'<div style="font-size:11px;color:{C_MUTED};font-family:Arial,sans-serif;">'
        f'Full intelligence bank &rarr; bank.json</div>'
        f'</td></tr>'
    )

    rows_html = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AEO Pulse — FrontlineHQ — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:{C_BG};font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:{C_BG};padding:20px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px;width:100%;background:{C_BG};padding:0 24px;">
          {rows_html}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ── Synthesis input builder ───────────────────────────────────────────────────

def _build_synthesis_input(
    fanout_results: list,
    extraction:     dict,
    citations:      list,
    ai_citations:   list,
    hypotheses:     list,
    sales_calls:    list,
    run_date:       str,
) -> str:
    lines = []

    us_hits  = sum(1 for c in citations if c.get("market") == "US" and c.get("frontlinehq_appears"))
    us_total = sum(1 for c in citations if c.get("market") == "US")
    perp_hits  = sum(1 for r in ai_citations if r.get("model") == "perplexity-sonar" and r.get("frontlinehq_appears"))
    perp_total = sum(1 for r in ai_citations if r.get("model") == "perplexity-sonar")
    cl_hits    = sum(1 for r in ai_citations if r.get("model") == "claude-web" and r.get("frontlinehq_appears"))
    cl_total   = sum(1 for r in ai_citations if r.get("model") == "claude-web")

    lines.append("=== CITATION RATES ===")
    lines.append(f"Google (Tavily) US: {us_hits} of {us_total} queries FrontlineHQ appears")
    if perp_total:
        lines.append(f"Perplexity (sonar): {perp_hits} of {perp_total} queries FrontlineHQ appears")
    if cl_total:
        lines.append(f"Claude (web search): {cl_hits} of {cl_total} queries FrontlineHQ appears")
    lines.append("")

    # AI engine competitor mentions
    if ai_citations:
        ai_comp_wins: dict = {}
        for r in ai_citations:
            for comp in r.get("competitors_cited", []):
                ai_comp_wins[comp] = ai_comp_wins.get(comp, 0) + 1
        if ai_comp_wins:
            lines.append("=== AI ENGINE COMPETITOR MENTIONS ===")
            for comp, n in sorted(ai_comp_wins.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"{comp}: cited in {n} AI responses")
            lines.append("")

    competitor_wins: dict = {}
    for c in citations:
        for comp in c.get("competitors_cited", []):
            competitor_wins[comp] = competitor_wins.get(comp, 0) + 1
    if competitor_wins:
        lines.append("=== COMPETITOR APPEARANCES ===")
        for comp, n in sorted(competitor_wins.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"{comp}: {n} queries")
        lines.append("")

    lines.append("=== FANOUT GAPS ===")
    for r in fanout_results:
        missing = r.get("frontlinehq_likely_missing", [])
        if missing:
            lines.append(f"Query: {r.get('query','')[:60]}")
            lines.append(f"  Missing: {', '.join(missing[:4])}")
            s = r.get("content_suggestion", "")
            if s and "FAILED" not in s:
                lines.append(f"  Suggestion: {s[:120]}")
    lines.append("")

    phrases = extraction.get("icp_phrases", [])[:10]
    lines.append(f"=== ICP PHRASES (top {len(phrases)}) ===")
    for p in phrases:
        lines.append(f'- "{p.get("text","")}" [{p.get("geography","?")}]')
    lines.append("")

    hooks = extraction.get("outbound_hooks", [])[:5]
    if hooks:
        lines.append("=== OUTBOUND HOOKS ===")
        for h in hooks:
            lines.append(f'- "{h.get("text","")}"')
        lines.append("")

    complaints = extraction.get("competitor_complaints", [])[:6]
    if complaints:
        lines.append("=== COMPETITOR COMPLAINTS ===")
        for c in complaints:
            lines.append(f'- {c.get("tool","")}: "{c.get("complaint","")}"')
        lines.append("")

    if hypotheses:
        lines.append("=== HYPOTHESES ===")
        for i, h in enumerate(hypotheses, 1):
            lines.append(f"[{i}] [{h.get('strength','?').upper()}] {h.get('hypothesis','')[:100]}")
            lines.append(f"     Action: {h.get('action','')[:100]}")
            lines.append(f"     Metric: {h.get('metric','')}")
        lines.append("")

    if sales_calls:
        lines.append("=== SALES CALL SIGNAL ===")
        for call in sales_calls[:5]:
            lines.append(f"Outcome: {call.get('outcome','?')} | Stage: {call.get('stage','?')}")
            for phrase in call.get("key_phrases", [])[:3]:
                lines.append(f'  "{phrase}"')
            if call.get("signal"):
                lines.append(f"  Signal: {call['signal']}")
        lines.append("")

    questions = extraction.get("unanswered_questions", [])[:5]
    if questions:
        lines.append("=== UNANSWERED QUESTIONS ===")
        for q in questions:
            lines.append(f"- {q}")
        lines.append("")

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_digest(
    fanout_results: list,
    extraction:     dict,
    citations:      list,
    hypotheses:     list,
    sales_calls:    list,
    next_queries:   list,
    run_date:       str,
    active_queries: list,
    ai_citations:   Optional[list] = None,
) -> str:
    """
    Generate the AEO digest as an HTML email.
    Claude produces structured JSON; Python builds the final HTML.
    """
    print("\n[synthesiser] Generating AEO digest...")
    if ai_citations is None:
        ai_citations = []

    synthesis_input = _build_synthesis_input(
        fanout_results, extraction, citations, ai_citations, hypotheses, sales_calls, run_date
    )

    user_message = (
        f"Today is {run_date[:10]}. Here is all the AEO pipeline data.\n\n"
        + synthesis_input
    )

    try:
        raw    = _call_claude(SYNTHESIS_SYSTEM_PROMPT, user_message, max_tokens=2048)
        parsed = _parse_json(raw)
        if not parsed:
            raise ValueError("Could not parse synthesis JSON")

        html = _build_html_email(parsed, next_queries, citations, ai_citations, run_date, active_queries)
        print("[synthesiser] Digest generated.")
        return html

    except anthropic.AuthenticationError:
        print("[synthesiser] ERROR: Invalid Anthropic API key.")
        raise
    except Exception as e:
        print(f"[synthesiser] ERROR: {e}")
        return _fallback_html(synthesis_input, run_date)


def generate_next_queries(
    extraction:     dict,
    fanout_results: list,
    sales_calls:    list,
) -> list:
    """Generate 5 next-run seed queries based on this run's findings."""
    print("\n[synthesiser] Generating next-run queries...")

    lines = []
    phrases = extraction.get("icp_phrases", [])[:8]
    if phrases:
        lines.append("New ICP language found:")
        for p in phrases:
            lines.append(f'  - "{p.get("text","")}"')

    complaints = extraction.get("competitor_complaints", [])[:4]
    if complaints:
        lines.append("Competitor gaps:")
        for c in complaints:
            lines.append(f'  - {c.get("tool","")}: "{c.get("complaint","")}"')

    missing_terms = []
    for r in fanout_results:
        missing_terms.extend(r.get("frontlinehq_likely_missing", []))
    if missing_terms:
        lines.append("Fanout terms FrontlineHQ is missing:")
        lines.append("  " + ", ".join(dict.fromkeys(missing_terms))[:300])

    if sales_calls:
        lines.append("Lost deal language from transcripts:")
        for call in sales_calls[:3]:
            for phrase in call.get("key_phrases", [])[:2]:
                lines.append(f'  - "{phrase}"')

    if not lines:
        lines.append("No data — generate queries based on general FrontlineHQ ICP pain points.")

    try:
        raw    = _call_claude(NEXT_QUERY_SYSTEM_PROMPT, "\n".join(lines), max_tokens=1024)
        parsed = _parse_json(raw)
        if parsed and isinstance(parsed, dict):
            queries = parsed.get("next_queries", [])
            print(f"[synthesiser] Generated {len(queries)} next-run queries.")
            return queries
        return []
    except anthropic.AuthenticationError:
        print("[synthesiser] ERROR: Invalid Anthropic API key.")
        raise
    except Exception as e:
        print(f"[synthesiser] Next query generation ERROR: {e}")
        return []


def _fallback_html(synthesis_input: str, run_date: str) -> str:
    date_str = run_date[:10]
    escaped  = synthesis_input.replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;padding:24px;color:#1a1a1a;">
  <h2>AEO Pulse — FrontlineHQ — {date_str}</h2>
  <p style="color:red;">[Claude synthesis unavailable — raw data below]</p>
  <pre style="font-size:12px;background:#f5f5f5;padding:16px;">{escaped}</pre>
</body></html>"""
