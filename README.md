# AEO Intelligence Bank — FrontlineHQ

A live intelligence dashboard and pipeline for Answer Engine Optimisation.

## What it does

The pipeline runs daily/on-demand to:
1. Generate fanout queries via Claude
2. Search Google (Tavily), Perplexity, and Claude (web search) for each seed query
3. Extract ICP language from Reddit and G2/Capterra
4. Process sales call transcripts
5. Generate hypotheses and next-run queries
6. Write everything to `bank.json`
7. Send a formatted HTML digest by email

The web app reads `bank.json` live on every page load — no redeployment needed.

## Run locally

```bash
cd aeo_system
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Run the pipeline

```bash
python run_aeo.py --dry-run   # test, no email, no save
python run_aeo.py             # full run — updates bank.json, sends email
```

After each pipeline run, refresh the browser to see updated data.

## Deploy to Railway

1. Push this directory (including `bank.json`) to a GitHub repo
2. Create a new Railway project → Deploy from GitHub
3. Set environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`
   - `TAVILY_API_KEY`
   - `RESEND_API_KEY`
   - `EMAIL_RECIPIENT`
   - `PERPLEXITY_API_KEY` (optional)
4. Railway auto-detects `Procfile` and runs `gunicorn app:app`

## File structure

```
aeo_system/
├── app.py                  Flask web app
├── run_aeo.py              Pipeline entry point
├── config.py               All settings and prompts
├── scraper.py              Tavily search
├── ai_citation_checker.py  Perplexity + Claude web checks
├── fanout.py               Fanout query generation
├── extractor.py            ICP language extraction
├── hypotheses.py           Hypothesis generation
├── synthesiser.py          Digest synthesis + HTML email
├── emailer.py              Resend email delivery
├── bank.py                 bank.json read/write
├── bank.json               Living intelligence bank
├── templates/index.html    Web UI
├── static/style.css        Styles
├── requirements.txt
├── Procfile
└── railway.json
```
