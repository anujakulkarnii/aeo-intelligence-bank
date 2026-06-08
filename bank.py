"""
AEO Intelligence System — Bank
Read/write operations for bank.json (the living language bank).
Never overwrites — always appends new findings with run dates.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from config import BANK_PATH, COMPANY, TARGET_MARKETS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return str(uuid.uuid4())[:8]


def load_bank() -> dict:
    """Load existing bank.json or return a fresh skeleton."""
    if os.path.exists(BANK_PATH):
        try:
            with open(BANK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[bank] Warning: could not load bank.json ({e}). Starting fresh.")

    return {
        "meta": {
            "company": COMPANY,
            "last_run": None,
            "run_count": 0,
            "markets": [m["name"] for m in TARGET_MARKETS],
            "geo_note": (
                "Phase 1 — US/UK via SearchAPI location parameter. "
                "Not VPN-based. Geographic precision is approximate. "
                "Phase 2 will add DACH with German language query variants "
                "and proxy-based geo execution."
            ),
            "steps_completed": [],
            "steps_failed": [],
        },
        "icp_phrases": [],
        "fanout_terms": [],
        "citations": [],
        "competitor_complaints": [],
        "outbound_hooks": [],
        "hypotheses": [],
        "sales_calls": [],
        "next_queries": [],
        "ai_citations": [],
        "digests": [],
    }


def save_bank(bank: dict) -> None:
    """Persist bank.json to disk."""
    try:
        with open(BANK_PATH, "w", encoding="utf-8") as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)
        print(f"[bank] Saved bank.json ({len(json.dumps(bank))} bytes)")
    except IOError as e:
        print(f"[bank] ERROR saving bank.json: {e}")


def merge_run_results(bank: dict, results: dict, run_date: str) -> dict:
    """
    Merge all results from a pipeline run into bank.
    results keys: fanout, icp, citations, hypotheses, sales_calls, digest
    """
    meta = bank["meta"]
    meta["last_run"]   = run_date
    meta["run_count"]  = meta.get("run_count", 0) + 1
    meta["steps_completed"] = results.get("steps_completed", [])
    meta["steps_failed"]    = results.get("steps_failed", [])

    # ── Fanout terms ──────────────────────────────────────────────────────────
    for fanout_item in results.get("fanout", []):
        query = fanout_item.get("query", "")
        for term in fanout_item.get("fanout_terms", []):
            bank["fanout_terms"].append({
                "id": _uid(),
                "term": term,
                "query": query,
                "frontlinehq_present": False,
                "teams": ["Product"],
                "run_date": run_date,
            })

    # ── ICP phrases ───────────────────────────────────────────────────────────
    existing_phrases = {p["text"] for p in bank["icp_phrases"]}
    for phrase in results.get("icp_phrases", []):
        if phrase.get("text") and phrase["text"] not in existing_phrases:
            bank["icp_phrases"].append({
                "id": _uid(),
                "text": phrase["text"],
                "source": phrase.get("source", "search"),
                "geography": phrase.get("geography", "Unknown"),
                "teams": phrase.get("teams", ["Sales"]),
                "run_date": run_date,
                "hot": True,
            })
            existing_phrases.add(phrase["text"])

    # ── Competitor complaints ─────────────────────────────────────────────────
    existing_complaints = {
        (c["tool"], c["complaint"]) for c in bank["competitor_complaints"]
    }
    for complaint in results.get("competitor_complaints", []):
        key = (complaint.get("tool", ""), complaint.get("complaint", ""))
        if key not in existing_complaints:
            bank["competitor_complaints"].append({
                "id": _uid(),
                "tool": complaint.get("tool", ""),
                "complaint": complaint.get("complaint", ""),
                "source": complaint.get("source", "search"),
                "run_date": run_date,
                "teams": ["Sales"],
            })
            existing_complaints.add(key)

    # ── Outbound hooks ────────────────────────────────────────────────────────
    existing_hooks = {h["text"] for h in bank["outbound_hooks"]}
    for hook in results.get("outbound_hooks", []):
        if hook.get("text") and hook["text"] not in existing_hooks:
            bank["outbound_hooks"].append({
                "id": _uid(),
                "text": hook["text"],
                "source": hook.get("source", "search"),
                "teams": hook.get("teams", ["Sales", "Social"]),
                "run_date": run_date,
            })
            existing_hooks.add(hook["text"])

    # ── Citations ─────────────────────────────────────────────────────────────
    for citation in results.get("citations", []):
        bank["citations"].append({
            "id": _uid(),
            "query": citation.get("query", ""),
            "market": citation.get("market", ""),
            "frontlinehq_appears": citation.get("frontlinehq_appears", False),
            "competitors_cited": citation.get("competitors_cited", []),
            "gap_analysis": citation.get("gap_analysis", ""),
            "run_date": run_date,
            "teams": ["Sales", "Product"],
        })

    # ── Hypotheses ────────────────────────────────────────────────────────────
    for hyp in results.get("hypotheses", []):
        bank["hypotheses"].append({
            "id": _uid(),
            "hypothesis": hyp.get("hypothesis", ""),
            "evidence": hyp.get("evidence", ""),
            "action": hyp.get("action", ""),
            "metric": hyp.get("metric", ""),
            "strength": hyp.get("strength", "weak"),
            "status": hyp.get("status", "planned"),
            "teams": hyp.get("teams", []),
            "generated_date": run_date,
            "result": None,
        })

    # ── Sales calls ───────────────────────────────────────────────────────────
    for call in results.get("sales_calls", []):
        bank["sales_calls"].append({
            "id": _uid(),
            "prospect": call.get("prospect", "Unknown"),
            "stage": call.get("stage", "unknown"),
            "outcome": call.get("outcome", "unknown"),
            "key_phrases": call.get("key_phrases", []),
            "objections": call.get("objections", []),
            "signal": call.get("signal", ""),
            "teams": ["Sales"],
            "date": run_date,
        })

    # ── Next queries ──────────────────────────────────────────────────────────
    if "next_queries" not in bank:
        bank["next_queries"] = []

    for nq in results.get("next_queries", []):
        bank["next_queries"].append({
            "id":             _uid(),
            "query":          nq.get("query", ""),
            "rationale":      nq.get("rationale", ""),
            "generated_date": run_date,
            "used":           False,
        })

    # ── AI Citations ──────────────────────────────────────────────────────────
    if "ai_citations" not in bank:
        bank["ai_citations"] = []

    for ac in results.get("ai_citations", []):
        bank["ai_citations"].append({
            "id":                  _uid(),
            "query":               ac.get("query", ""),
            "model":               ac.get("model", ""),
            "frontlinehq_appears": ac.get("frontlinehq_appears", False),
            "competitors_cited":   ac.get("competitors_cited", []),
            "sources":             ac.get("sources", []),
            "response_preview":    ac.get("response_preview", ""),
            "date":                ac.get("date", run_date),
            "run_date":            run_date,
        })

    # ── Digest ────────────────────────────────────────────────────────────────
    if results.get("digest"):
        bank["digests"].append({
            "run_date": run_date,
            "content": results["digest"],
        })

    return bank


def load_pending_next_queries(bank: dict) -> list:
    """
    Return all next_queries not yet used, and mark them as used.
    Called at the start of a run so they feed into the active seed set.
    """
    pending = [
        nq for nq in bank.get("next_queries", [])
        if not nq.get("used", False)
    ]
    for nq in pending:
        nq["used"] = True
    return pending


def print_bank_summary(bank: dict) -> None:
    meta = bank["meta"]
    print(f"\n[bank] Summary:")
    print(f"  Run count      : {meta.get('run_count', 0)}")
    print(f"  Last run       : {meta.get('last_run', 'never')}")
    print(f"  ICP phrases    : {len(bank['icp_phrases'])}")
    print(f"  Fanout terms   : {len(bank['fanout_terms'])}")
    print(f"  Citations      : {len(bank['citations'])}")
    print(f"  Complaints     : {len(bank['competitor_complaints'])}")
    print(f"  Outbound hooks : {len(bank['outbound_hooks'])}")
    print(f"  Hypotheses     : {len(bank['hypotheses'])}")
    print(f"  Sales calls    : {len(bank['sales_calls'])}")
    print(f"  Next queries   : {len(bank.get('next_queries', []))}")
    print(f"  AI citations   : {len(bank.get('ai_citations', []))}")
    print(f"  Digests        : {len(bank['digests'])}")
