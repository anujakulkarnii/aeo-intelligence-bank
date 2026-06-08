"""
AEO Intelligence System — AI Citation Checker
Queries Perplexity (sonar) and Claude (with web search) directly to check
whether FrontlineHQ appears in AI-generated tool recommendations.
"""

import time
from datetime import datetime, timezone
from typing import Optional

import requests
import anthropic

from config import (
    PERPLEXITY_API_KEY,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    COMPETITORS,
)

PERPLEXITY_ENDPOINT = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL    = "sonar"


# ── Shared helpers ────────────────────────────────────────────────────────────

def _question_for(query: str) -> str:
    return (
        f"What are the best tools for: {query}? "
        "Give me specific software product recommendations with brief reasons."
    )


def _detect_frontlinehq(text: str) -> bool:
    return "frontlinehq" in text.lower()


def _detect_competitors(text: str) -> list:
    text_lower = text.lower()
    return [c for c in COMPETITORS if c.lower() in text_lower]


# ── Perplexity ────────────────────────────────────────────────────────────────

def _query_perplexity(question: str) -> Optional[dict]:
    """POST to Perplexity sonar. Returns raw JSON or None."""
    if not PERPLEXITY_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model":    PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": question}],
    }

    try:
        resp = requests.post(
            PERPLEXITY_ENDPOINT, json=payload, headers=headers, timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"[ai_checker] Perplexity HTTP error: {e} — {resp.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"[ai_checker] Perplexity request error: {e}")
    return None


def _extract_perplexity_result(raw: dict, query: str) -> dict:
    """Pull text + citations from a Perplexity response."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        text    = raw["choices"][0]["message"]["content"]
        sources = raw.get("citations", [])
        if isinstance(sources, list):
            sources = [s if isinstance(s, str) else s.get("url", "") for s in sources]
    except (KeyError, IndexError, TypeError):
        text    = ""
        sources = []

    return {
        "query":               query,
        "model":               "perplexity-sonar",
        "frontlinehq_appears": _detect_frontlinehq(text),
        "competitors_cited":   _detect_competitors(text),
        "sources":             sources[:5],
        "response_preview":    text[:300],
        "date":                now,
    }


# ── Claude with web search ────────────────────────────────────────────────────

def _query_claude_web(question: str) -> Optional[str]:
    """
    Query Claude with the built-in web_search tool.
    Handles the multi-turn tool_use loop automatically.
    Returns the final response text or None on failure.
    """
    if not ANTHROPIC_API_KEY:
        return None

    try:
        client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        messages = [{"role": "user", "content": question}]
        tools    = [{"type": "web_search_20250305", "name": "web_search"}]

        for _round in range(6):
            resp = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                tools=tools,
                messages=messages,
            )

            # Collect any text blocks
            text_parts = [b.text for b in resp.content if hasattr(b, "text") and b.text]

            if resp.stop_reason == "end_turn":
                return "\n".join(text_parts)

            if resp.stop_reason == "tool_use":
                # Add assistant turn
                messages.append({"role": "assistant", "content": resp.content})
                # Build tool_result stubs — server-side tool, content auto-filled
                tool_results = [
                    {
                        "type":        "tool_result",
                        "tool_use_id": b.id,
                        "content":     "",
                    }
                    for b in resp.content
                    if getattr(b, "type", None) == "tool_use"
                ]
                if not tool_results:
                    break
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason — return whatever text we have
                if text_parts:
                    return "\n".join(text_parts)
                break

    except anthropic.APIError as e:
        print(f"[ai_checker] Claude web search API error: {e}")
    except Exception as e:
        print(f"[ai_checker] Claude web search error: {e}")

    return None


def _extract_claude_result(text: Optional[str], query: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    if not text:
        return {
            "query":               query,
            "model":               "claude-web",
            "frontlinehq_appears": False,
            "competitors_cited":   [],
            "sources":             [],
            "response_preview":    "",
            "date":                now,
        }
    return {
        "query":               query,
        "model":               "claude-web",
        "frontlinehq_appears": _detect_frontlinehq(text),
        "competitors_cited":   _detect_competitors(text),
        "sources":             [],  # Claude web doesn't surface structured citations
        "response_preview":    text[:300],
        "date":                now,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def run_ai_citation_checks(queries: list) -> list:
    """
    For each seed query, query Perplexity and Claude (web search).
    Returns a flat list of citation records, one per (query × model).

    Gracefully skips engines whose API key is not configured.
    """
    results = []
    perp_enabled  = bool(PERPLEXITY_API_KEY)
    claude_enabled = bool(ANTHROPIC_API_KEY)

    if not perp_enabled:
        print("[ai_checker] PERPLEXITY_API_KEY not set — skipping Perplexity checks.")
    if not claude_enabled:
        print("[ai_checker] ANTHROPIC_API_KEY not set — skipping Claude web checks.")

    total = len(queries) * (int(perp_enabled) + int(claude_enabled))
    done  = 0

    print(
        f"\n[ai_checker] Running {total} AI citation checks "
        f"({len(queries)} queries × "
        f"{'Perplexity + ' if perp_enabled else ''}{'Claude web' if claude_enabled else ''})..."
    )

    for query in queries:
        question = _question_for(query)

        # ── Perplexity ────────────────────────────────────────────────────────
        if perp_enabled:
            done += 1
            print(f"  [{done}/{total}] Perplexity: {query[:60]}...")
            raw = _query_perplexity(question)
            if raw:
                results.append(_extract_perplexity_result(raw, query))
            else:
                results.append(_extract_perplexity_result({}, query))
            time.sleep(0.5)

        # ── Claude web search ─────────────────────────────────────────────────
        if claude_enabled:
            done += 1
            print(f"  [{done}/{total}] Claude web: {query[:60]}...")
            text = _query_claude_web(question)
            results.append(_extract_claude_result(text, query))
            time.sleep(0.5)

    perp_hits   = sum(1 for r in results if r["model"] == "perplexity-sonar" and r["frontlinehq_appears"])
    perp_total  = sum(1 for r in results if r["model"] == "perplexity-sonar")
    claude_hits  = sum(1 for r in results if r["model"] == "claude-web" and r["frontlinehq_appears"])
    claude_total = sum(1 for r in results if r["model"] == "claude-web")

    if perp_total:
        print(f"[ai_checker] Perplexity: FrontlineHQ in {perp_hits}/{perp_total} queries")
    if claude_total:
        print(f"[ai_checker] Claude web: FrontlineHQ in {claude_hits}/{claude_total} queries")

    return results
