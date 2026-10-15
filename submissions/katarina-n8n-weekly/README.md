# Weekly GitHub developer summary with n8n + Claude + Discord

**Bounty:** upstream issue #5 (advertised $200, conditional on acceptance and payment).

An importable eight-node n8n workflow. Every Friday at 17:00 (Asia/Jakarta), it gathers the last seven days of GitHub commits, closed issues (excluding PR issues), and merged pull requests, asks Claude for a concise narrative in English or French, and posts it into Discord.

## Setup (five steps)

1. Import workflow.json into a **self-hosted n8n instance** (Workflows > Add workflow > Import from file).
2. Open the **Setup** Code node and set owner, repo and language (EN or FR). The workflow throws an actionable error while placeholders remain.
3. Configure your n8n host environment variables ANTHROPIC_API_KEY and DISCORD_WEBHOOK_URL. Restart the n8n process so they become available to expressions. Do not put either secret inside the workflow JSON; ensure environment-variable access is allowed in n8n (for example N8N_BLOCK_ENV_ACCESS_IN_NODE=false in supported self-hosted setups).
4. Manually execute the workflow with a public GitHub repository. Confirm the commits, closed issues and merged PRs are counted correctly and a message appears in the specified Discord channel. A private GitHub repository needs an authenticated GitHub HTTP credential added to the three fetch nodes; unauthenticated mode is intentionally public-only.
5. Activate the workflow after the manual test. Execution timezone is Asia/Jakarta; change it in Workflow Settings for another region.

## Workflow

- **Weekly Schedule:** Weekly Friday 17:00.
- **Setup:** Validates GitHub owner/repo/language and computes UTC ISO week window.
- **Fetch Commits / Fetch Closed Issues / Fetch Closed PRs:** Three GitHub REST GET requests; each is executeOnce and emits empty data rather than terminating on zero results.
- **Build Prompt:** Filters records by commit/close/merge date; removes PR issues from issue totals, summarizes three counts, and warns when 100-result endpoint caps could omit events.
- **Claude Weekly Summary:** Anthropic Messages API, model claude-sonnet-4-20250514, with no stored API key.
- **Discord Weekly Report:** Sends one message to the configured webhook, capping the narrative to 1,750 characters to stay under Discord's 2,000-character content limit.

**Language:** Set language to FR in Setup for French or EN for English. **Destination:** Set DISCORD_WEBHOOK_URL to a webhook created in your preferred Discord channel. **Repository:** Edit owner and repo. GitHub public API calls need no token; rate limits apply.

## Testing

Run: node test_workflow.cjs (Node.js 18+); the suite validates importable JSON structure, all connections, weekly schedule, environment-based secrets, no duplicate GitHub calls for arrays, correct filtering, empty periods and truncation warnings. Tests are pure Node with mocked GitHub outputs; **no external network and no cost**. GitHub Actions runs the same tests.

**Not yet validated:** live n8n import/execution with real GitHub/Anthropic/Discord credentials. The bounty specifically requires a screenshot of a successful real n8n execution; this submission does not include one, and it must be provided before claiming full acceptance. No API keys or screenshots have been fabricated.

**Data / operational limitations:** GitHub endpoints fetch up to 100 results each rather than paging. At exactly 100 items the report says results may be incomplete. The closed-PR endpoint sorts by last update, so under heavy activity some merged PRs might be missed. Source titles and commit subjects are untrusted input to the language model. Claude outputs may contain inaccuracies and should be reviewed before distribution. Self-hosted env access must be restricted to trusted workflow editors.

**Cost:** Anthropic API calls can incur usage charges. GitHub REST unauthenticated access is rate limited. Discord webhooks can be revoked in Discord if compromised.
