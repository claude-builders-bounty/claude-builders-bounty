# n8n Weekly GitHub Summary with Claude

This submission provides an importable n8n workflow that runs every Friday at 17:00, collects the last week's GitHub repository activity, asks Claude (`claude-sonnet-4-20250514`) for a narrative summary, and delivers the result to Discord by default or email when configured.

## Files

- `workflows/n8n-weekly-dev-summary.json` — importable n8n workflow export.
- `README-n8n-weekly-dev-summary.md` — setup, configuration, and validation notes.

## Five-step setup

1. Import the workflow:
   ```bash
   n8n import:workflow --input workflows/n8n-weekly-dev-summary.json
   ```
2. Configure environment variables in your n8n deployment:
   - `GITHUB_REPO=owner/repo`
   - `GITHUB_TOKEN=<GitHub token with read access>`
   - `ANTHROPIC_API_KEY=<Claude API key>`
   - `SUMMARY_LANGUAGE=EN` or `FR`
   - `DELIVERY_MODE=discord` or `email`
3. Configure the destination:
   - Discord: set `DISCORD_WEBHOOK_URL`.
   - Email: set `EMAIL_TO`, `EMAIL_FROM`, and n8n SMTP credentials for the Email Send node.
4. In n8n, open the imported workflow and confirm the credentials/environment values are visible to the HTTP Request and Email nodes.
5. Execute the workflow manually once, confirm delivery, then activate it for the weekly Friday 17:00 trigger.

## What the workflow does

1. `Weekly Friday 17:00` triggers once per week.
2. `Build Config` derives the repo, time window, destination, and language from environment variables.
3. Three GitHub API requests fetch:
   - commits since the start of the 7-day window,
   - closed issues since the start of the 7-day window,
   - merged PRs from GitHub Search for the same repository and week.
4. `Prepare Claude Prompt` validates that all GitHub responses are arrays/search results, filters closed issues and merged PRs to the exact 7-day window, and fails loudly if a fetch is malformed instead of letting Claude summarize partial data silently.
5. `Claude Narrative Summary` calls Anthropic's Messages API with model `claude-sonnet-4-20250514`.
6. `Format Delivery` creates a Discord payload and an email subject/body.
7. `Delivery Mode Email?` routes to Discord webhook delivery by default, or email when `DELIVERY_MODE=email`.

## Configuration reference

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `GITHUB_REPO` | yes | `n8n-io/n8n` | Repository to summarize. |
| `GITHUB_TOKEN` | recommended | `ghp_...` | Avoids low unauthenticated rate limits; needs read-only repo access. |
| `ANTHROPIC_API_KEY` | yes | `sk-ant-...` | Calls Claude Sonnet 4. |
| `SUMMARY_LANGUAGE` | no | `EN` / `FR` | Summary language, default `EN`. |
| `DELIVERY_MODE` | no | `discord` / `email` | Destination route, default `discord`. |
| `DISCORD_WEBHOOK_URL` | for Discord | `https://discord.com/api/webhooks/...` | Webhook target. |
| `EMAIL_TO` | for email | `team@example.com` | Email recipient. |
| `EMAIL_FROM` | for email | `n8n@example.com` | Email sender address. |

## Validation performed

Because this cron job cannot safely use a real Anthropic key or private webhook, validation is static/offline rather than a live paid API execution. The checks verify that the workflow is parseable JSON, has the required n8n node types, contains the Friday weekly trigger, calls GitHub commits/issues/merged-PR endpoints, uses `claude-sonnet-4-20250514`, supports EN/FR via `SUMMARY_LANGUAGE`, contains Discord and email delivery paths, and keeps `continueOnFail:false` on API/delivery nodes so failures do not become misleading green summaries.

Run locally:

```bash
python3 tests/validate_n8n_workflow.py
```

Expected output:

```text
n8n workflow validation passed
```

## Screenshot / real-instance note

The bounty requests a screenshot from a real n8n instance. I did not fabricate one and did not spend or expose credentials. The workflow is ready to import; the validation above is the evidence I can produce autonomously in this environment. A maintainer can reproduce the final green run by importing the JSON, setting the environment variables, and clicking **Execute workflow** in n8n.
