"""
AEO Intelligence System — Main Entry Point

Usage:
  python run_aeo.py           # Full run: write bank.json + send email
  python run_aeo.py --dry-run # Print all outputs, no writes, no email
"""

import sys
import os
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    ANTHROPIC_API_KEY,
    TAVILY_API_KEY,
    RESEND_API_KEY,
    EMAIL_RECIPIENT,
    ANTHROPIC_MODEL,
    SEED_QUERIES,
)


def _check_config() -> list:
    warnings = []
    if not TAVILY_API_KEY:
        warnings.append("TAVILY_API_KEY not set — search steps will be skipped")
    if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 20:
        warnings.append("ANTHROPIC_API_KEY appears invalid — Claude steps will fail")
    if not RESEND_API_KEY:
        warnings.append("RESEND_API_KEY not set — email will be skipped")
    if not EMAIL_RECIPIENT:
        warnings.append("EMAIL_RECIPIENT not set — email will be skipped")
    return warnings


def _section(title: str) -> None:
    print(f"\n{'━' * 50}")
    print(f"  {title}")
    print('━' * 50)


def run(dry_run: bool = False) -> None:
    run_date = datetime.now(timezone.utc).isoformat()

    _section(f"AEO Intelligence System — {'DRY RUN' if dry_run else 'FULL RUN'}")
    print(f"Run date : {run_date[:10]}")
    print(f"Model    : {ANTHROPIC_MODEL}")
    print(f"Dry run  : {dry_run}")

    warnings = _check_config()
    if warnings:
        print("\n⚠  Configuration warnings:")
        for w in warnings:
            print(f"   • {w}")

    steps_completed: list = []
    steps_failed:    list = []

    results: dict = {
        "fanout":                [],
        "icp_phrases":           [],
        "unanswered_questions":  [],
        "competitor_complaints": [],
        "outbound_hooks":        [],
        "citations":             [],
        "ai_citations":          [],
        "hypotheses":            [],
        "sales_calls":           [],
        "next_queries":          [],
        "digest":                "",
        "steps_completed":       steps_completed,
        "steps_failed":          steps_failed,
    }

    # ─────────────────────────────────────────────────────────────────────────
    # PRE-RUN — Load pending next_queries from bank and merge into seed set
    # ─────────────────────────────────────────────────────────────────────────
    active_queries = list(SEED_QUERIES)   # start with configured seeds
    pending_next_queries = []

    if not dry_run:
        try:
            from bank import load_bank, load_pending_next_queries
            _bank_preload = load_bank()
            pending_next_queries = load_pending_next_queries(_bank_preload)
            if pending_next_queries:
                extra = [nq["query"] for nq in pending_next_queries if nq.get("query")]
                active_queries = list(dict.fromkeys(active_queries + extra))
                print(f"\n[run] Loaded {len(extra)} pending next-run queries from bank.")
                for q in extra:
                    print(f"  + {q[:70]}")
        except Exception as e:
            print(f"[run] Could not load pending queries from bank: {e}")
    else:
        print(f"\n[run] DRY RUN — using configured seed queries only ({len(active_queries)} queries).")

    print(f"[run] Active seed queries this run: {len(active_queries)}")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1 — Fanout generation
    # ─────────────────────────────────────────────────────────────────────────
    _section(f"STEP 1 / 8 — Fanout Query Generation ({len(active_queries)} queries)")
    fanout_results = []
    try:
        from fanout import run_fanout_generation
        fanout_results    = run_fanout_generation(active_queries)
        results["fanout"] = fanout_results
        steps_completed.append("fanout")

        if fanout_results:
            sample = fanout_results[0]
            print(f"\n[step 1] Sample:")
            print(f"  Query   : {sample.get('query','')[:60]}")
            print(f"  Fanout  : {', '.join(sample.get('fanout_terms',[])[:4])}")
            print(f"  Missing : {', '.join(sample.get('frontlinehq_likely_missing',[])[:3])}")

    except Exception as e:
        print(f"[step 1] FAILED: {e}")
        steps_failed.append("fanout")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 — Geo-specific searches
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 2 / 8 — Geo-Specific Seed Query Searches")
    citations = []
    try:
        from scraper import run_geo_searches
        citations            = run_geo_searches(active_queries)
        results["citations"] = citations
        steps_completed.append("geo_searches")

        us_hits = sum(1 for c in citations if c.get("market") == "US" and c.get("frontlinehq_appears"))
        us_tot  = sum(1 for c in citations if c.get("market") == "US")
        print(f"\n[step 2] US: FrontlineHQ in {us_hits}/{us_tot} queries")

    except Exception as e:
        print(f"[step 2] FAILED: {e}")
        steps_failed.append("geo_searches")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2b — AI Engine Citation Checks (Perplexity + Claude web)
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 2b / 8 — AI Engine Citation Checks")
    ai_citations = []
    try:
        from ai_citation_checker import run_ai_citation_checks
        ai_citations             = run_ai_citation_checks(active_queries)
        results["ai_citations"]  = ai_citations
        steps_completed.append("ai_citations")

        perp_hits  = sum(1 for r in ai_citations if r["model"] == "perplexity-sonar" and r["frontlinehq_appears"])
        perp_tot   = sum(1 for r in ai_citations if r["model"] == "perplexity-sonar")
        cl_hits    = sum(1 for r in ai_citations if r["model"] == "claude-web" and r["frontlinehq_appears"])
        cl_tot     = sum(1 for r in ai_citations if r["model"] == "claude-web")
        if perp_tot:
            print(f"\n[step 2b] Perplexity: {perp_hits}/{perp_tot} | Claude: {cl_hits}/{cl_tot}")

    except Exception as e:
        print(f"[step 2b] FAILED: {e}")
        steps_failed.append("ai_citations")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3 — Reddit + competitor review scraping
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 3 / 8 — Reddit & Competitor Review Searches")
    reddit_results = []
    review_results = []
    try:
        from scraper import run_reddit_searches, run_competitor_review_searches
        reddit_results = run_reddit_searches()
        review_results = run_competitor_review_searches()
        steps_completed.append("community_searches")
        print(f"\n[step 3] Reddit: {len(reddit_results)} | Reviews: {len(review_results)}")

    except Exception as e:
        print(f"[step 3] FAILED: {e}")
        steps_failed.append("community_searches")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4 — ICP language extraction
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 4 / 8 — ICP Language Extraction")
    extraction: dict = {
        "icp_phrases": [], "unanswered_questions": [],
        "competitor_complaints": [], "outbound_hooks": [],
    }
    try:
        from extractor import extract_icp_language
        extraction = extract_icp_language(reddit_results, review_results)
        results["icp_phrases"]           = extraction.get("icp_phrases", [])
        results["unanswered_questions"]  = extraction.get("unanswered_questions", [])
        results["competitor_complaints"] = extraction.get("competitor_complaints", [])
        results["outbound_hooks"]        = extraction.get("outbound_hooks", [])
        steps_completed.append("icp_extraction")

        print(f"\n[step 4] {len(results['icp_phrases'])} phrases | "
              f"{len(results['competitor_complaints'])} complaints | "
              f"{len(results['outbound_hooks'])} hooks")

        for p in results["icp_phrases"][:3]:
            print(f'    [{p.get("geography","?")}] "{p.get("text","")[:80]}"')

    except Exception as e:
        print(f"[step 4] FAILED: {e}")
        steps_failed.append("icp_extraction")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4b — Sales call transcripts
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 4b / 8 — Sales Call Transcript Processing")
    sales_calls = []
    try:
        from extractor import process_transcripts
        sales_calls            = process_transcripts()
        results["sales_calls"] = sales_calls
        if sales_calls:
            steps_completed.append("transcripts")
            print(f"[step 4b] Processed {len(sales_calls)} transcript(s).")
            for call in sales_calls[:3]:
                print(f"  {call.get('source_file','?')} | {call.get('outcome','?')} | {call.get('signal','')[:80]}")
        else:
            print("[step 4b] No transcripts found — skipped.")

    except Exception as e:
        print(f"[step 4b] FAILED: {e}")
        steps_failed.append("transcripts")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5 — Hypothesis generation
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 5 / 8 — Hypothesis Generation")
    hypotheses = []
    try:
        from hypotheses import generate_hypotheses
        hypotheses            = generate_hypotheses(
            fanout_results=fanout_results,
            extraction=extraction,
            citations=citations,
            sales_calls=sales_calls,
        )
        results["hypotheses"] = hypotheses
        steps_completed.append("hypotheses")

        print(f"\n[step 5] {len(hypotheses)} hypothesis(es):")
        for i, h in enumerate(hypotheses, 1):
            print(f"  [{i}] [{h.get('strength','?').upper()}] {h.get('hypothesis','')[:80]}")

    except Exception as e:
        print(f"[step 5] FAILED: {e}")
        steps_failed.append("hypotheses")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 6 — Next query generation
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 6 / 8 — Next-Run Query Generation")
    next_queries = []
    try:
        from synthesiser import generate_next_queries
        next_queries            = generate_next_queries(
            extraction=extraction,
            fanout_results=fanout_results,
            sales_calls=sales_calls,
        )
        results["next_queries"] = next_queries
        steps_completed.append("next_queries")

        print(f"\n[step 6] {len(next_queries)} next-run queries generated:")
        for i, nq in enumerate(next_queries, 1):
            print(f"  [{i}] {nq.get('query','')[:70]}")
            print(f"       Why: {nq.get('rationale','')[:80]}")

    except Exception as e:
        print(f"[step 6] FAILED: {e}")
        steps_failed.append("next_queries")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 7 — Digest synthesis
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 7 / 8 — Digest Synthesis")
    digest = ""
    try:
        from synthesiser import generate_digest
        digest            = generate_digest(
            fanout_results=fanout_results,
            extraction=extraction,
            citations=citations,
            ai_citations=ai_citations,
            hypotheses=hypotheses,
            sales_calls=sales_calls,
            next_queries=next_queries,
            run_date=run_date,
            active_queries=active_queries,
        )
        results["digest"] = digest
        steps_completed.append("synthesis")

        print("\n" + "─" * 60)
        print(digest)
        print("─" * 60)

    except Exception as e:
        print(f"[step 7] FAILED: {e}")
        steps_failed.append("synthesis")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 8 — Write bank.json + send email
    # ─────────────────────────────────────────────────────────────────────────
    _section("STEP 8 / 8 — Persist & Notify")

    if dry_run:
        print("[step 8] DRY RUN — skipping bank.json write and email send.")
        print(f"\n  Steps completed : {', '.join(steps_completed) or 'none'}")
        print(f"  Steps failed    : {', '.join(steps_failed) or 'none'}")
    else:
        try:
            from bank import load_bank, merge_run_results, save_bank, print_bank_summary
            bank = load_bank()
            bank = merge_run_results(bank, results, run_date)
            save_bank(bank)
            steps_completed.append("bank_write")
            print_bank_summary(bank)
        except Exception as e:
            print(f"[step 8] bank.json write FAILED: {e}")
            steps_failed.append("bank_write")
            traceback.print_exc()

        if digest:
            try:
                from emailer import send_digest
                sent = send_digest(digest, run_date)
                if sent:
                    steps_completed.append("email")
                else:
                    steps_failed.append("email")
            except Exception as e:
                print(f"[step 8] Email FAILED: {e}")
                steps_failed.append("email")
                traceback.print_exc()
        else:
            print("[step 8] No digest generated — skipping email.")

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("RUN COMPLETE")
    print(f"  Completed : {', '.join(steps_completed) or 'none'}")
    print(f"  Failed    : {', '.join(steps_failed) or 'none'}")
    print(f"\n  {'✓ All steps succeeded.' if not steps_failed else f'⚠  {len(steps_failed)} step(s) failed.'}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)
