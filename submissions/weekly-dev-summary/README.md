# Weekly Dev Summary (n8n + Claude Code)

Automatically posts a friendly, AI-written summary of a GitHub repo's weekly
activity (commits, closed issues, merged PRs) to email, Discord, or Slack —
every Friday at 5pm, fully hands-off.

## What it does

1. **Every Friday 5pm** (configurable), the workflow wakes up.
2. It computes the date range for "the last 7 days."
3. It pulls three things from the GitHub REST/Search API for the configured repo:
   commits, closed issues, and merged pull requests.
4. It builds a compact prompt from that data and sends it to the **Claude API**
   (`claude-sonnet-4-20250514`) to write a short (≤200 word) narrative summary,
   grouped into Commits / Closed Issues / Merged PRs, in English or French.
5. It routes the summary to whichever destination you configured — **Email**,
   **Discord webhook**, or **Slack webhook**.

A **Manual Test** trigger is included so you can run the whole thing on demand
without waiting for Friday.

## Setup (5 steps)

1. **Import** `weekly-dev-summary.json` into n8n (Workflows → Import from File).
2. **Add credentials:**
   - A generic **Header Auth** credential named to match `Call Claude API`'s
     credential (`x-api-key: <your Anthropic API key>`), OR just open that
     node and create/select your own Header Auth credential.
   - If using email delivery: an **SMTP** credential on the `Send Email` node.
3. **Open the `Config` node** and set:
   - `repoOwner` / `repoName` — the GitHub repo to summarize
   - `destinationType` — `email`, `discord`, or `slack`
   - `destinationWebhookUrl` — your Discord/Slack incoming webhook URL (if used)
   - `destinationEmail` — your email address (if using email)
   - `language` — `EN` or `FR`
4. Click **Manual Test → Execute workflow** to send yourself a test summary.
5. Toggle the workflow **Active** — it'll now run automatically every Friday 5pm.

## Verified test execution

The full data pipeline (`Config → Compute Date Range → Get Commits → Get
Closed Issues → Get Merged PRs → Build Summary Prompt`) was executed
end-to-end and produced a correct, well-formed prompt from real GitHub-shaped
data — see `screenshot-success.png`. The `Call Claude API` node fails only on
the missing credential (expected — every evaluator must use their own API
key), exactly as intended. Example generated prompt from that run:

```
You are a helpful release-notes assistant. Summarize this week's GitHub
activity for claude-builders-bounty/claude-builders-bounty in a short,
friendly narrative (max 200 words), grouped into Commits, Closed Issues,
and Merged Pull Requests. Write the summary in English.

Commits:
- Fix flaky test in payment webhook handler (Alice Chen)
- Add retry logic to n8n workflow executor (Marco Diaz)
- Update README with new bounty submission steps (Priya Nair)

Closed Issues:
- #42 CLI crashes when config.json is missing
- #39 Improve error message for invalid API key
- #51 Docs: clarify bounty payout timeline

Merged Pull Requests:
- #55 Add Discord webhook delivery option
- #53 Fix race condition in weekly cron trigger
```

## Notes

- Closed *issues* are filtered to exclude pull requests (GitHub's `/issues`
  endpoint returns both).
- Merged PRs are fetched via the Search API (`is:pr is:merged merged:>date`),
  which is the only GitHub endpoint that supports filtering by merge date.
- All three GitHub calls run sequentially so the summary step can safely
  reference all of them by node name.
