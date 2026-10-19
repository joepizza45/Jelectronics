# Jelectronics

A daily, AI-curated feed of price errors and exceptional sales on electronics (laptops, tablets, monitors, TVs and more) from Amazon, Costco and Best Buy.

Three Claude agents run in sequence every day:

| Agent | File | Job |
|---|---|---|
| **Scout** | `agents/scout.py` | Searches the web widely (deal forums, price trackers, retailer deal pages) for price glitches and deep discounts, traces each one to the retailer's product page, and grabs a product image. |
| **Verifier** | `agents/verifier.py` | Opens each candidate on the live retailer page, checks price, stock and the "regular price" claim, and marks it `verified`, `uncertain` or `rejected` with a confidence score. |
| **Publisher** | `agents/publisher.py` | Keeps only verified deals with confidence ≥ 60, writes headlines and a daily summary, picks a featured deal, and writes `site/data/deals.json` (plus a dated copy in `site/data/archive/`). |

The site in `site/` is static HTML/CSS/JS that reads `deals.json`, so it can be hosted anywhere. A GitHub Actions workflow runs the pipeline daily and deploys the site to GitHub Pages.

## Setup

1. **API key:** in the GitHub repo, go to *Settings → Secrets and variables → Actions* and add `ANTHROPIC_API_KEY`.
2. **Pages:** in *Settings → Pages*, set *Source* to **GitHub Actions**.
3. **Run it:** *Actions → Daily deals update → Run workflow*, or wait for the daily schedule (12:17 UTC). Each run commits the new data and redeploys the site.

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline.py                     # scout -> verify -> publish
python -m http.server -d site 8000     # view at http://localhost:8000
```

Each run saves the raw agent output to `runs/<timestamp>/`. To regenerate the site from a saved run without new searches: `python pipeline.py --from-run runs/<timestamp>`.

## Configuration

- Model: `claude-opus-5-5` by default; override with the `JELECTRONICS_MODEL` env var.
- Search budgets: `web_tools(...)` calls in `scout.py` and `verifier.py` (`max_uses` caps cost per run).
- Publish threshold: `MIN_CONFIDENCE` in `publisher.py`.
- Schedule: the `cron` line in `.github/workflows/daily.yml`.

## Notes

- The repo ships with clearly labeled sample data; the first pipeline run replaces it.
- Product images are hot-linked from retailer CDNs. If one fails to load, the card shows a neutral placeholder.
- Price errors are often cancelled by retailers, and Costco member pricing may not be visible to the verifier (those come back `uncertain` and are not published).
- If you later add affiliate links (e.g. Amazon Associates), you must add the required disclosure to the site footer.
