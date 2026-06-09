"""
AEO Intelligence System — ICP Language Extractor
Uses Claude to extract ICP phrases, competitor complaints,
outbound hooks, and unanswered questions from scraped results.
"""

import json
from typing import Optional, Union
import anthropic

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    ICP_EXTRACTOR_SYSTEM_PROMPT,
    TRANSCRIPT_SYSTEM_PROMPT,
    TRANSCRIPTS_DIR,
)
from scraper import format_results_for_extraction

import os


def _call_claude(system_prompt: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _parse_json(raw: str) -> Optional[Union[dict, list]]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[extractor] JSON parse error: {e}\nRaw snippet: {raw[:300]}")
        return None


def _chunk_results(results: list[dict], chunk_size: int = 20) -> list[list[dict]]:
    """Split result list into chunks to avoid exceeding token limits."""
    return [results[i:i + chunk_size] for i in range(0, len(results), chunk_size)]


def extract_icp_language(
    reddit_results: list[dict],
    review_results: list[dict],
) -> dict:
    """
    Run ICP extraction over Reddit and review site results.
    Returns aggregated extraction dict.
    """
    combined = reddit_results + review_results
    if not combined:
        print("[extractor] No results to extract from.")
        return {
            "icp_phrases": [],
            "unanswered_questions": [],
            "competitor_complaints": [],
            "outbound_hooks": [],
        }

    all_phrases      = []
    all_questions    = []
    all_complaints   = []
    all_hooks        = []

    chunks = _chunk_results(combined, chunk_size=20)
    print(f"\n[extractor] Extracting ICP language from {len(combined)} results in {len(chunks)} chunk(s)...")

    for i, chunk in enumerate(chunks, 1):
        print(f"  [chunk {i}/{len(chunks)}] {len(chunk)} results...")
        text_block = format_results_for_extraction(chunk)

        # Build a geography context hint from the chunk's geography tags
        chunk_geos = list({r.get("geography", "Unknown") for r in chunk if r.get("geography")})
        if len(chunk_geos) == 1:
            geo_hint = f"NOTE: All results in this batch are from {chunk_geos[0]}. Tag geography accordingly."
        elif chunk_geos:
            geo_hint = f"NOTE: Results in this batch include mixed geographies: {', '.join(sorted(chunk_geos))}. Use the geography field from the search context to tag each entry accurately."
        else:
            geo_hint = ""

        user_message = (
            "Here are search result snippets from Reddit and review sites. "
            "Extract ICP language as instructed.\n"
            + (f"{geo_hint}\n" if geo_hint else "")
            + "\n"
            + text_block
        )

        try:
            raw    = _call_claude(ICP_EXTRACTOR_SYSTEM_PROMPT, user_message)
            parsed = _parse_json(raw)

            if not parsed or not isinstance(parsed, dict):
                print(f"  [chunk {i}] Unexpected response structure, skipping.")
                continue

            # Tag each phrase with source info
            source_tags = list({r.get("source", "search") for r in chunk})
            source      = source_tags[0] if len(source_tags) == 1 else "mixed"

            for phrase in parsed.get("icp_phrases", []):
                phrase["source"] = source
                all_phrases.append(phrase)

            all_questions.extend(parsed.get("unanswered_questions", []))

            for c in parsed.get("competitor_complaints", []):
                c["source"] = source
                all_complaints.append(c)

            for hook in parsed.get("outbound_hooks", []):
                hook["source"] = source
                all_hooks.append(hook)

        except anthropic.AuthenticationError:
            print("[extractor] ERROR: Invalid Anthropic API key.")
            raise
        except Exception as e:
            print(f"  [chunk {i}] ERROR: {e}")
            continue

    print(f"[extractor] Done. "
          f"{len(all_phrases)} phrases, "
          f"{len(all_questions)} questions, "
          f"{len(all_complaints)} complaints, "
          f"{len(all_hooks)} hooks.")

    return {
        "icp_phrases":           all_phrases,
        "unanswered_questions":  list(dict.fromkeys(all_questions)),
        "competitor_complaints": all_complaints,
        "outbound_hooks":        all_hooks,
    }


def process_transcripts() -> list[dict]:
    """
    Read all .txt files from /transcripts and extract signal via Claude.
    Returns list of sales call dicts.
    """
    if not os.path.isdir(TRANSCRIPTS_DIR):
        print("[extractor] No transcripts folder found, skipping.")
        return []

    txt_files = [
        f for f in os.listdir(TRANSCRIPTS_DIR)
        if f.endswith(".txt")
    ]

    if not txt_files:
        print("[extractor] No .txt files in transcripts folder, skipping.")
        return []

    print(f"\n[extractor] Processing {len(txt_files)} transcript(s)...")
    calls = []

    for fname in txt_files:
        fpath = os.path.join(TRANSCRIPTS_DIR, fname)
        print(f"  Processing: {fname}")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                print(f"  Skipping empty file: {fname}")
                continue

            user_message = (
                f"Here is a sales call transcript from file '{fname}':\n\n"
                + content[:6000]   # cap at ~1500 tokens
            )

            raw    = _call_claude(TRANSCRIPT_SYSTEM_PROMPT, user_message)
            parsed = _parse_json(raw)

            if parsed and isinstance(parsed, dict):
                parsed["source_file"] = fname
                calls.append(parsed)
            else:
                print(f"  Could not parse response for {fname}")

        except anthropic.AuthenticationError:
            print("[extractor] ERROR: Invalid Anthropic API key.")
            raise
        except Exception as e:
            print(f"  ERROR processing {fname}: {e}")
            continue

    print(f"[extractor] Transcript processing done. {len(calls)} call(s) extracted.")
    return calls
