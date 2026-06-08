"""
AEO Intelligence System — Hypothesis Generator
Uses Claude to synthesise all pipeline data into 3 actionable hypotheses.
"""

import json
from typing import Optional
import anthropic

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    HYPOTHESIS_SYSTEM_PROMPT,
)
from fanout import summarise_missing_terms


def _call_claude(system_prompt: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _parse_json(raw: str) -> Optional[list]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[hypotheses] JSON parse error: {e}\nRaw: {raw[:300]}")
        return None


def _build_context(
    fanout_results:        list[dict],
    extraction:            dict,
    citations:             list[dict],
    sales_calls:           list[dict],
) -> str:
    """
    Build a structured context string for the hypothesis prompt.
    """
    lines = []

    # ── Citation summary ──────────────────────────────────────────────────────
    us_hits = sum(1 for c in citations if c.get("market") == "US" and c.get("frontlinehq_appears"))
    uk_hits = sum(1 for c in citations if c.get("market") == "UK" and c.get("frontlinehq_appears"))
    us_total = sum(1 for c in citations if c.get("market") == "US")
    uk_total = sum(1 for c in citations if c.get("market") == "UK")

    competitor_wins = {}
    for c in citations:
        for comp in c.get("competitors_cited", []):
            competitor_wins[comp] = competitor_wins.get(comp, 0) + 1

    lines.append("=== CITATION DATA ===")
    lines.append(f"US: FrontlineHQ appears in {us_hits}/{us_total} queries")
    lines.append(f"UK: FrontlineHQ appears in {uk_hits}/{uk_total} queries")
    if competitor_wins:
        sorted_comps = sorted(competitor_wins.items(), key=lambda x: x[1], reverse=True)
        lines.append("Competitor appearances: " + ", ".join(f"{c}({n})" for c, n in sorted_comps))
    lines.append("")

    # ── Missing fanout terms ──────────────────────────────────────────────────
    missing = summarise_missing_terms(fanout_results)[:20]
    lines.append("=== FANOUT GAPS (FrontlineHQ likely missing) ===")
    lines.append(", ".join(missing) if missing else "None detected")
    lines.append("")

    # ── ICP phrases (top 10) ─────────────────────────────────────────────────
    phrases = extraction.get("icp_phrases", [])[:10]
    lines.append("=== TOP ICP PHRASES FROM REDDIT/REVIEWS ===")
    for p in phrases:
        lines.append(f'- "{p.get("text", "")}" [{p.get("geography", "Unknown")}]')
    lines.append("")

    # ── Competitor complaints (top 10) ────────────────────────────────────────
    complaints = extraction.get("competitor_complaints", [])[:10]
    lines.append("=== COMPETITOR COMPLAINTS ===")
    for c in complaints:
        lines.append(f'- {c.get("tool", "Unknown")}: "{c.get("complaint", "")}"')
    lines.append("")

    # ── Sales call signal ─────────────────────────────────────────────────────
    if sales_calls:
        lines.append("=== SALES CALL SIGNAL ===")
        for call in sales_calls[:5]:
            lines.append(f"Outcome: {call.get('outcome', 'unknown')} | Stage: {call.get('stage', 'unknown')}")
            for phrase in call.get("key_phrases", [])[:3]:
                lines.append(f'  "{phrase}"')
            if call.get("signal"):
                lines.append(f"  Signal: {call['signal']}")
        lines.append("")

    # ── Content suggestions from fanout ──────────────────────────────────────
    suggestions = [
        r.get("content_suggestion", "")
        for r in fanout_results
        if r.get("content_suggestion") and "FAILED" not in r.get("content_suggestion", "")
    ][:5]
    if suggestions:
        lines.append("=== CONTENT SUGGESTIONS FROM FANOUT ===")
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def generate_hypotheses(
    fanout_results:  list[dict],
    extraction:      dict,
    citations:       list[dict],
    sales_calls:     list[dict],
) -> list[dict]:
    """
    Generate 3 hypotheses from all pipeline data.
    Returns list of hypothesis dicts.
    """
    print("\n[hypotheses] Generating hypotheses...")

    context = _build_context(fanout_results, extraction, citations, sales_calls)
    user_message = (
        "Here is the aggregated AEO data from this pipeline run. "
        "Generate 3 hypotheses as instructed.\n\n"
        + context
    )

    try:
        raw    = _call_claude(HYPOTHESIS_SYSTEM_PROMPT, user_message)
        parsed = _parse_json(raw)

        if not parsed or not isinstance(parsed, list):
            print("[hypotheses] Unexpected response — returning empty list.")
            return []

        print(f"[hypotheses] Generated {len(parsed)} hypothesis(es).")
        return parsed

    except anthropic.AuthenticationError:
        print("[hypotheses] ERROR: Invalid Anthropic API key.")
        raise
    except Exception as e:
        print(f"[hypotheses] ERROR: {e}")
        return []
