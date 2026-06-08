"""
AEO Intelligence System — Scraper
All search calls via Tavily API: seed queries, Reddit searches,
competitor review searches.
"""

import time
import requests
from typing import Optional

from config import (
    TAVILY_API_KEY,
    TAVILY_BASE_URL,
    RESULTS_PER_QUERY,
    SEED_QUERIES,
    TARGET_MARKETS,
    REDDIT_SEARCHES,
    COMPETITOR_REVIEW_SEARCHES,
    COMPETITORS,
)


def _search(
    query: str,
    max_results: int = RESULTS_PER_QUERY,
    search_depth: str = "basic",
) -> Optional[dict]:
    """
    Single Tavily search call. Returns raw response dict or None on failure.
    search_depth: "basic" (1 credit) or "advanced" (2 credits).
    """
    if not TAVILY_API_KEY:
        print("[scraper] ERROR: TAVILY_API_KEY not set.")
        return None

    payload = {
        "api_key":      TAVILY_API_KEY,
        "query":        query,
        "max_results":  max_results,
        "search_depth": search_depth,
        "include_answer": False,
    }

    try:
        resp = requests.post(TAVILY_BASE_URL, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"[scraper] HTTP error for '{query[:60]}': {e} — {resp.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"[scraper] Request error for '{query[:60]}': {e}")
    except Exception as e:
        print(f"[scraper] Unexpected error for '{query[:60]}': {e}")
    return None


def _extract_results(raw: dict, max_results: int = RESULTS_PER_QUERY) -> list[dict]:
    """
    Pull results from a Tavily response.
    Returns list of {title, snippet, url, date}.
    """
    if not raw:
        return []
    results = []
    for item in raw.get("results", [])[:max_results]:
        results.append({
            "title":   item.get("title", ""),
            "snippet": item.get("content", ""),
            "url":     item.get("url", ""),
            "date":    item.get("published_date", ""),
        })
    return results


def _detect_competitors(results: list[dict]) -> list[str]:
    """Check which known competitors appear in result titles/snippets."""
    mentioned = set()
    for r in results:
        combined = (r.get("title", "") + " " + r.get("snippet", "")).lower()
        for comp in COMPETITORS:
            if comp.lower() in combined:
                mentioned.add(comp)
    return list(mentioned)


def run_geo_searches(queries: list = None) -> list[dict]:
    """
    Run all seed queries for configured markets (US only in Phase 1).
    Accepts an optional queries list (defaults to SEED_QUERIES from config).
    Returns list of citation records.
    """
    if queries is None:
        queries = SEED_QUERIES

    citations = []
    total = len(queries) * len(TARGET_MARKETS)
    done  = 0

    print(f"\n[scraper] Running {total} geo seed query searches "
          f"({len(queries)} queries × {len(TARGET_MARKETS)} market)...")

    for market in TARGET_MARKETS:
        for query in queries:
            done += 1
            print(f"  [{done}/{total}] {market['name']}: {query[:60]}...")

            raw     = _search(query, max_results=RESULTS_PER_QUERY)
            results = _extract_results(raw)

            all_text = " ".join(
                r.get("title", "") + " " + r.get("snippet", "") + " " + r.get("url", "")
                for r in results
            ).lower()
            frontlinehq_appears = "frontlinehq" in all_text
            competitors_cited   = _detect_competitors(results)

            if competitors_cited and not frontlinehq_appears:
                gap = f"Competitors {', '.join(competitors_cited)} cited; FrontlineHQ absent"
            elif not results:
                gap = "No results returned (API error or quota)"
            else:
                gap = "FrontlineHQ not directly cited; opportunity exists"

            citations.append({
                "query":               query,
                "market":              market["name"],
                "frontlinehq_appears": frontlinehq_appears,
                "competitors_cited":   competitors_cited,
                "gap_analysis":        gap,
                "results":             results,
            })

            time.sleep(0.2)

    print(f"[scraper] Geo searches complete. {len(citations)} records.")
    return citations


def run_reddit_searches() -> list[dict]:
    """
    Run Reddit-specific searches via Tavily.
    Returns flat list of result dicts tagged source='reddit'.
    """
    all_results = []
    print(f"\n[scraper] Running {len(REDDIT_SEARCHES)} Reddit searches...")

    for i, query in enumerate(REDDIT_SEARCHES, 1):
        print(f"  [{i}/{len(REDDIT_SEARCHES)}] {query[:70]}...")
        raw     = _search(query, max_results=RESULTS_PER_QUERY)
        results = _extract_results(raw)
        for r in results:
            r["source"]       = "reddit"
            r["search_query"] = query
        all_results.extend(results)
        time.sleep(0.2)

    print(f"[scraper] Reddit searches returned {len(all_results)} results.")
    return all_results


def run_competitor_review_searches() -> list[dict]:
    """
    Run G2/Capterra competitor review searches via Tavily.
    Returns flat list of result dicts tagged source='review_site'.
    """
    all_results = []
    print(f"\n[scraper] Running {len(COMPETITOR_REVIEW_SEARCHES)} competitor review searches...")

    for i, query in enumerate(COMPETITOR_REVIEW_SEARCHES, 1):
        print(f"  [{i}/{len(COMPETITOR_REVIEW_SEARCHES)}] {query[:70]}...")
        raw     = _search(query, max_results=RESULTS_PER_QUERY)
        results = _extract_results(raw)
        for r in results:
            r["source"]       = "review_site"
            r["search_query"] = query
        all_results.extend(results)
        time.sleep(0.2)

    print(f"[scraper] Competitor review searches returned {len(all_results)} results.")
    return all_results


def format_results_for_extraction(results: list[dict]) -> str:
    """
    Format result list into a compact text block for the ICP extractor prompt.
    """
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', '')} | {r.get('url', '')}")
        snippet = r.get("snippet", "").strip()
        if snippet:
            lines.append(f"    {snippet[:400]}")
        lines.append("")
    return "\n".join(lines)
