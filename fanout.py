"""
AEO Intelligence System — Fanout Generator
Uses Claude to generate fanout query expansions for each seed query.
"""

import json
from typing import Optional, Union
import anthropic

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    FANOUT_SYSTEM_PROMPT,
    SEED_QUERIES,
)


def _call_claude(system_prompt: str, user_message: str) -> str:
    """Single Claude API call. Returns raw text response."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _parse_json_response(raw: str) -> Optional[Union[dict, list]]:
    """
    Attempt to parse JSON from Claude's response.
    Strips any accidental markdown fences.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # drop first line (```json) and last line (```)
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[fanout] JSON parse error: {e}\nRaw: {raw[:300]}")
        return None


def generate_fanout_for_query(query: str) -> Optional[dict]:
    """
    Generate fanout analysis for a single seed query.
    Returns parsed dict or None on failure.
    """
    user_message = f'Analyse this seed query:\n\n"{query}"'
    try:
        raw    = _call_claude(FANOUT_SYSTEM_PROMPT, user_message)
        parsed = _parse_json_response(raw)
        if parsed and isinstance(parsed, dict):
            # ensure query field is present
            parsed.setdefault("query", query)
            return parsed
        print(f"[fanout] Unexpected response structure for: {query}")
        return None
    except anthropic.AuthenticationError:
        print("[fanout] ERROR: Invalid Anthropic API key.")
        raise
    except Exception as e:
        print(f"[fanout] ERROR for query '{query[:50]}': {e}")
        return None


def run_fanout_generation(queries: Optional[list] = None) -> list[dict]:
    """
    Run fanout generation for all seed queries (or a provided list).
    Returns list of fanout dicts. Failed queries are skipped.
    """
    if queries is None:
        queries = SEED_QUERIES

    results = []
    print(f"\n[fanout] Generating fanout for {len(queries)} seed queries...")

    for i, query in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {query[:60]}...")
        fanout = generate_fanout_for_query(query)
        if fanout:
            results.append(fanout)
        else:
            # Append a placeholder so we don't silently lose queries
            results.append({
                "query": query,
                "fanout_terms": [],
                "proof_types_needed": [],
                "frontlinehq_likely_missing": [],
                "content_suggestion": "FAILED — check API key / quota",
            })

    print(f"[fanout] Done. {sum(1 for r in results if r.get('fanout_terms'))} succeeded.")
    return results


def summarise_missing_terms(fanout_results: list[dict]) -> list[str]:
    """
    Flatten all frontlinehq_likely_missing terms across all queries.
    Used for hypothesis generation context.
    """
    missing = []
    for r in fanout_results:
        missing.extend(r.get("frontlinehq_likely_missing", []))
    return list(dict.fromkeys(missing))   # deduplicate while preserving order
