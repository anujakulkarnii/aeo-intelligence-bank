"""
AEO Intelligence System — Configuration
All settings, prompts, seed queries, markets, and competitor lists.

Run modes (on-demand only — no scheduling):
  python run_aeo.py --dry-run   test, no email, no save
  python run_aeo.py             full run, email + save
"""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── API Keys ──────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY     = os.getenv("TAVILY_API_KEY", "")
RESEND_API_KEY     = os.getenv("RESEND_API_KEY", "")
EMAIL_RECIPIENT    = os.getenv("EMAIL_RECIPIENT", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

ANTHROPIC_MODEL = "claude-sonnet-4-5"

# ── Company Context ───────────────────────────────────────────────────────────

COMPANY = "FrontlineHQ"

PRODUCT_DESCRIPTION = """
AI-native frontline operations platform for multi-location hospitality and retail.
Helps operators standardise training, maintain consistency across locations,
onboard staff faster, and give area managers visibility into where execution
breaks down before it hits revenue. Fictional stand-in for a real Series A
company. Similar profile to Bounti (Berlin), Axonify, Beekeeper, Bindy.
"""

# ── Seed Queries (top 5 for demo — Phase 2 adds remaining 5) ─────────────────

SEED_QUERIES = [
    "training quality depends on who happens to train new staff",
    "how to standardise training across multiple restaurant locations",
    "grew fast now I don't know who is doing what where",
    "replace notion and slack for managing frontline teams",
    "staff onboarding program from scratch restaurant",
]

# ── Target Markets (US only — Phase 2 adds UK) ───────────────────────────────

TARGET_MARKETS = [
    {
        "name": "US",
        "country": "us",
        "location": "New York, United States",
    },
]

# ── Competitors ───────────────────────────────────────────────────────────────

COMPETITORS = [
    "Deputy",
    "Axonify",
    "Bindy",
    "Workforce.com",
    "Beekeeper",
    "Connecteam",
    "7shifts",
]

# ── Reddit Search Strings ─────────────────────────────────────────────────────

REDDIT_SEARCHES = [
    'site:reddit.com "restaurant training" "multiple locations"',
    'site:reddit.com "frontline staff" "consistency" "locations"',
    'site:reddit.com "staff onboarding" "restaurant" problem',
    'site:reddit.com "training program" "from scratch" restaurant',
    'site:reddit.com Deputy OR Axonify complaints',
    'site:reddit.com "workforce management" "grown fast"',
    'site:reddit.com "policies procedures" restaurant locations',
]

# ── Competitor Review Searches ────────────────────────────────────────────────

COMPETITOR_REVIEW_SEARCHES = [
    "site:g2.com Deputy reviews frontline",
    "site:g2.com Axonify reviews",
    "site:g2.com Beekeeper reviews complaints",
    "site:capterra.com Deputy alternative restaurant",
    "site:capterra.com Axonify complaints",
]

# ── Tavily ────────────────────────────────────────────────────────────────────

TAVILY_BASE_URL    = "https://api.tavily.com/search"
RESULTS_PER_QUERY  = 3   # max 3 for demo (vs 5 in production)

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
BANK_PATH        = os.path.join(BASE_DIR, "bank.json")
TRANSCRIPTS_DIR  = os.path.join(BASE_DIR, "..", "transcripts")

# ── System Prompts ────────────────────────────────────────────────────────────

FANOUT_SYSTEM_PROMPT = """You are an AI search behaviour analyst specialising in B2B SaaS and frontline operations software.

Simulate how AI engines like Perplexity, Claude, and ChatGPT expand user queries in the background before generating an answer. These background searches are called fanout queries — terms the AI adds that the user never typed.

Company: FrontlineHQ
Product: AI-native frontline ops platform for multi-location hospitality and retail

For each seed query:

1. List 5-7 fanout terms AI would add in background searches — be specific not generic
2. Identify proof types AI looks for in this category: case studies with metrics, ROI data, compliance certifications, analyst reports, comparison pages, video demos, customer testimonials with specifics
3. Flag which fanout terms FrontlineHQ is likely NOT present in based on typical early-stage startup content gaps
4. Suggest one specific content angle to fix the biggest gap — include format, angle, target query

Return JSON only. No preamble. Schema:
{
  "query": "original query",
  "fanout_terms": ["term1", "term2"],
  "proof_types_needed": ["type1", "type2"],
  "frontlinehq_likely_missing": ["term1", "term2"],
  "content_suggestion": "specific actionable suggestion"
}"""

ICP_EXTRACTOR_SYSTEM_PROMPT = """You are an ICP language analyst for FrontlineHQ — a B2B SaaS targeting multi-location hospitality and retail operators.

Read these search result snippets from Reddit and review sites.

Extract:

1. EXACT PHRASES describing operational problems
   — keep messy authentic language, do not polish
   — these should sound like something said at 11pm in frustration, not a marketing brief

2. UNANSWERED QUESTIONS — content gap signals
   Questions being asked that nobody is answering well in search results

3. COMPETITOR COMPLAINTS — tool name plus exact complaint language from the reviewer

4. OUTBOUND HOOKS — phrases so specific and painful they would stop a COO mid-scroll in a cold email subject line. Ready to use, not to edit.

5. GEOGRAPHY SIGNALS — tag each entry:
   US / UK / EU / Unknown
   Based on: currency mentioned, specific chains, regulations (GDPR vs CCPA), states/counties, language patterns

6. TEAM RELEVANCE — tag each entry:
   Sales: outbound hooks, competitor complaints, lost deal language
   Social: ICP phrases for content, emotional frustrations, relatable moments
   Product: process gaps, feature requests, tool switching reasons

Return JSON only. No preamble. Schema:
{
  "icp_phrases": [
    {
      "text": "...",
      "geography": "US/UK/EU/Unknown",
      "teams": ["Sales","Social","Product"]
    }
  ],
  "unanswered_questions": ["..."],
  "competitor_complaints": [
    {"tool": "...", "complaint": "..."}
  ],
  "outbound_hooks": [
    {
      "text": "...",
      "teams": ["Sales","Social"]
    }
  ]
}"""

HYPOTHESIS_SYSTEM_PROMPT = """You are a senior GTM strategist and AEO specialist for FrontlineHQ.

You have access to:
- Citation data: which queries FrontlineHQ appears in vs which competitors appear instead
- Fanout terms FrontlineHQ is missing
- ICP language extracted from Reddit and review sites
- Competitor complaint data from G2/Capterra
- Lost deal language from sales call transcripts

Generate 3 intelligent hypotheses. Each must:
- Be grounded in specific data from the inputs above
- Cite which evidence supports it
- Recommend a specific content action (not vague — include format, angle, target query)
- Identify one leading metric to track
- Estimate signal strength: strong / medium / weak
- Specify which team owns it: Sales / Social / Product

A strong hypothesis has direct evidence from at least two data sources. A weak one is speculative.

Do not generate generic hypotheses like "publish more content." Every hypothesis must be specific enough that someone could act on it tomorrow.

Return JSON only. Schema:
[
  {
    "hypothesis": "...",
    "evidence": "What data supports this",
    "action": "Specific content to create or change",
    "metric": "One leading indicator to track",
    "strength": "strong/medium/weak",
    "status": "planned",
    "teams": ["Product","Sales"]
  }
]"""

SYNTHESIS_SYSTEM_PROMPT = """You are an AEO strategist for FrontlineHQ.

You have just received pipeline data including fanout analysis, ICP language from Reddit/reviews, competitor data, and hypotheses.

Return JSON only. No preamble. Schema:
{
  "content_gaps": [
    {
      "gap": "short title max 22 chars",
      "why_losing": "brief reason max 22 chars",
      "action": "specific action max 22 chars",
      "timeline": "X days"
    }
  ],
  "outbound_hooks": [
    "full hook text ready to use as-is",
    "full hook text ready to use as-is"
  ],
  "top_hypothesis": {
    "hypothesis": "one clear sentence",
    "action": "specific content to create",
    "metric": "one leading indicator to track",
    "strength": "strong/medium/weak",
    "timeline": "X days"
  },
  "icp_phrases_highlight": [
    "exact phrase 1",
    "exact phrase 2",
    "exact phrase 3",
    "exact phrase 4"
  ],
  "competitor_alert": "one paragraph or null if nothing significant"
}"""

NEXT_QUERY_SYSTEM_PROMPT = """You are an AEO strategist for FrontlineHQ.

You just completed a pipeline run and found the data below.

Based on what you learned this run, generate 5 new seed queries to test next run.

Rules:
- Written in authentic messy ICP language
- Not polished marketing terms
- Should test angles we haven't covered yet
- Prioritise queries where competitors are weak or where ICP language is specific and painful

Return JSON only. No preamble. Schema:
{
  "next_queries": [
    {
      "query": "...",
      "rationale": "one sentence why this query matters"
    }
  ]
}"""

TRANSCRIPT_SYSTEM_PROMPT = """You are an ICP language analyst extracting signal from a sales call transcript for FrontlineHQ.

Extract:
1. Exact phrases the prospect used to describe their problem — keep raw authentic language
2. Questions they asked during the call
3. Objections raised
4. Tools or competitors they mentioned
5. Whether the deal converted or was lost
6. Stage reached before going cold

Tag extracted phrases with:
- source: "sales_call"
- outcome: "converted" or "lost"
- teams: ["Sales"]

Return JSON only. Schema:
{
  "prospect": "company or person name if mentioned, else Unknown",
  "stage": "discovery/demo/proposal/negotiation/unknown",
  "outcome": "lost/converted/unknown",
  "key_phrases": ["exact phrase 1", "exact phrase 2"],
  "questions_asked": ["..."],
  "objections": ["..."],
  "competitors_mentioned": ["..."],
  "signal": "one-line summary of what this call tells us about ICP pain"
}"""
