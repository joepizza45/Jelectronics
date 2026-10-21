# Daily deals run (Claude Code)

This is the no-API-key way to run Jelectronics: a scheduled Claude Code session runs the three agents as subagents on your Claude subscription, then pushes the new data, and GitHub Pages redeploys the site.

Steps for the session doing the run:

1. `git checkout main && git pull origin main`, then `pip install -q -r requirements.txt`.
2. Make the run directory: `runs/<YYYY-MM-DD>/` (today's date, UTC).
3. Spawn the **deal-scout** subagent. Tell it today's date, the output path `runs/<date>/scout.json`, and the deal ids already on the site (the `id` fields in `site/data/deals.json`, skip them if `"sample": true`) and the recently rejected ids (the keys of `site/data/rejected.json`, if it exists).
4. When it finishes, spawn the **deal-verifier** subagent with the scout.json path and output path `runs/<date>/verifier.json`.
5. Write `runs/<date>/publisher.json` (or spawn the **deal-publisher** subagent with the run directory). Only verified deals need headlines, so this step is small.
6. Build the site data: `python pipeline.py --from-run runs/<date>`. This needs no API key because publisher.json is present.
7. Commit only `site/data/` to **main** with the message `Daily deals update <date>` and `git push origin main`. Pushing to main is intended here: it is what triggers the site deploy.
8. Reply with one line: deals published, how many were rejected, and the featured headline.

If the scout finds nothing or every candidate is rejected, still run steps 6-7 so the site shows that day's empty state.
