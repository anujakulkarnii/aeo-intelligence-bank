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
    country: str = None,
    location: str = None,
) -> Optional[dict]:
    """
    Single Tavily search call. Returns raw response dict or None on failure.
    search_depth: "basic" (1 credit) or "advanced" (2 credits).
    country: optional ISO country code (e.g. "us", "gb") for geo-targeting.
    location: optional location string (e.g. "London, United Kingdom").
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
    if country:
        payload["country"] = country
    if location:
        payload["location"] = location

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
    Run all seed queries for configured markets.
    Accepts an optional queries list (used as fallback for markets without seed_queries).
    Returns list of citation records.
    """
    if queries is None:
        queries = SEED_QUERIES

    citations = []
    # Calculate total considering per-market seed_queries
    total = sum(len(m.get("seed_queries", queries)) for m in TARGET_MARKETS)
    done  = 0

    print(f"\n[scraper] Running {total} geo seed query searches "
          f"({len(TARGET_MARKETS)} market(s))...")

    for market in TARGET_MARKETS:
        market_queries = market.get("seed_queries", queries)
        for query in market_queries:
            done += 1
            print(f"  [{done}/{total}] {market['name']}: {query[:60]}...")

            raw     = _search(
                query,
                max_results=RESULTS_PER_QUERY,
                country=market.get("country"),
                location=market.get("location"),
            )
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


def run_reddit_searches(market: dict = None) -> list[dict]:
    """
    Run Reddit-specific searches via Tavily.
    If market is provided and has 'reddit_searches', use those; otherwise use global REDDIT_SEARCHES.
    Returns flat list of result dicts tagged source='reddit' and geography=market name.
    """
    if market and market.get("reddit_searches"):
        searches = market["reddit_searches"]
        geo_tag  = market["name"]
        country  = market.get("country")
    else:
        searches = REDDIT_SEARCHES
        geo_tag  = "US" if not market else market.get("name", "Unknown")
        country  = market.get("country") if market else None

    all_results = []
    label = f"{geo_tag} Reddit" if market else "Reddit"
    print(f"\n[scraper] Running {len(searches)} {label} searches...")

    for i, query in enumerate(searches, 1):
        print(f"  [{i}/{len(searches)}] {query[:70]}...")
        raw     = _search(query, max_results=RESULTS_PER_QUERY, country=country)
        results = _extract_results(raw)
        for r in results:
            r["source"]       = "reddit"
            r["search_query"] = query
            r["geography"]    = geo_tag
        all_results.extend(results)
        time.sleep(0.2)

    print(f"[scraper] {label} searches returned {len(all_results)} results.")
    return all_results


def run_competitor_review_searches(market: dict = None) -> list[dict]:
    """
    Run G2/Capterra competitor review searches via Tavily.
    Passes market country for geo-targeting and tags results with geography.
    Returns flat list of result dicts tagged source='review_site'.
    """
    geo_tag = market["name"] if market else "US"
    country = market.get("country") if market else None

    all_results = []
    label = f"{geo_tag} competitor reviews" if market else "competitor reviews"
    print(f"\n[scraper] Running {len(COMPETITOR_REVIEW_SEARCHES)} {label} searches...")

    for i, query in enumerate(COMPETITOR_REVIEW_SEARCHES, 1):
        print(f"  [{i}/{len(COMPETITOR_REVIEW_SEARCHES)}] {query[:70]}...")
        raw     = _search(query, max_results=RESULTS_PER_QUERY, country=country)
        results = _extract_results(raw)
        for r in results:
            r["source"]       = "review_site"
            r["search_query"] = query
            r["geography"]    = geo_tag
        all_results.extend(results)
        time.sleep(0.2)

    print(f"[scraper] {label} searches returned {len(all_results)} results.")
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
