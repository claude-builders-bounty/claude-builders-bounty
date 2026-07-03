# Weekly GitHub Dev Summary (n8n + Claude)

Importable [n8n](https://n8n.io) workflow that generates a **narrative weekly dev summary** for any GitHub repository using Claude (`claude-sonnet-4-20250514`), then delivers it via **Discord**, **Slack**, or **email**.

## Setup (5 steps)

### 1. Import the workflow

Load the exportable JSON into n8n so all 13 nodes (trigger, GitHub fetches, Claude, delivery) are available for configuration.

In n8n: **Workflows → Import from File** → select `weekly-dev-summary.json`.

### 2. Configure environment variables

Define repo, API keys, and delivery destination in n8n **Settings → Variables** (self-hosted `.env` or n8n Cloud variables):

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_REPO` | ✅ | Target repo as `owner/repo` |
| `GITHUB_TOKEN` | ✅ | GitHub PAT with repo read access |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `DELIVERY_CHANNEL` | ✅ | `discord`, `slack`, or `email` |
| `DISCORD_WEBHOOK_URL` | if discord | Discord incoming webhook |
| `SLACK_WEBHOOK_URL` | if slack | Slack incoming webhook |
| `SUMMARY_EMAIL_TO` | if email | Recipient address (validated as email format in Load Config) |
| `SUMMARY_EMAIL_FROM` | if email | Sender address (default: `n8n@localhost`) |
| `SUMMARY_LANGUAGE` | optional | `EN` (default) or `FR` |

For email delivery, attach an **SMTP** credential to the **Send Email** node.

**Security:** Store `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and webhook URLs in n8n **Variables** or your host `.env` — never commit them to git or paste them into workflow nodes. The workflow reads secrets only via `$env.*` at runtime. **Load Config** validates `GITHUB_TOKEN` can read the configured repo via `GET https://api.github.com/repos/{owner}/{repo}` before any activity fetches, and fails fast if required keys are missing or invalid. Use least-privilege GitHub PATs (repo read) and rotate keys if exposed.

**Secrets manager (production):** For self-hosted n8n, prefer injecting credentials from an external secrets store rather than plain `.env` files on disk:

- **n8n Credentials / Variables** — built-in encrypted store (n8n Cloud or self-hosted with encryption key)
- **HashiCorp Vault** — mount secrets into n8n container env at startup (`vault kv get -field=...`)
- **AWS Secrets Manager / GCP Secret Manager** — sync to runtime env via your orchestrator (Docker/K8s secrets)

Map vault paths to the same `$env` names (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, webhook URLs). The workflow never embeds secret values in JSON — only `$env` references at execution time.

**Pre-flight token check** (recommended before first run):

```bash
GITHUB_TOKEN=<your-token> GITHUB_REPO=owner/repo npm run test:validate-token
```

This sends a test request to GitHub's repo API and exits non-zero if the token is missing, invalid, or lacks read access.

### 3. Verify the schedule

Confirm the cron matches your team's timezone — default is Friday 17:00 in workflow timezone `America/New_York`.

Open **Friday 5pm Weekly Trigger** and confirm timezone/day/hour (default: Friday 17:00, workflow timezone `America/New_York`).

### 4. Test run

Execute once manually to verify GitHub data collection, Claude summarization, and delivery to your chosen channel.

Click **Execute Workflow**. Confirm GitHub nodes return data, Claude returns a summary, and delivery succeeds.

### 5. Activate

Enable the weekly schedule so summaries run automatically every Friday at 5pm.

Toggle the workflow **Active** to enable the weekly cron.

## What it does

```
Friday 5pm Trigger → Load Config → parallel GitHub fetches (commits, issues, merged PRs)
  → Merge → Build Claude Prompt → Claude API → Format Summary → Route Delivery
      → Discord | Slack | Email
```

- Fetches the past 7 days of commits, closed issues, and merged PRs (filtered by date)
- GitHub fetch Code nodes **paginate** (`per_page=100` loop) so active repos are not truncated at 100 items
- GitHub fetch failures **fail fast** (no `continueRegularOutput` swallowing auth/404/rate-limit errors into summaries)
- Secrets stay in **`$env.*` only** — Load Config never copies tokens or webhook URLs into n8n execution item JSON
- Builds a structured prompt with contributor stats
- Generates EN/FR narrative via Claude Sonnet 4 (Claude API errors fall back to a stats-only summary)
- Delivers formatted output to your chosen channel

## Validation

### CI workflow (`test-n8n-weekly-summary.yml`)

GitHub Actions runs three jobs (working directory: `workflows/n8n-weekly-dev-summary`):

| Job | npm script | What it tests |
|-----|------------|---------------|
| `validate` | `test:ci` | Full local regression: workflow JSON structure, GitHub collect helpers, Claude summary, delivery channels, fleet delivery gates, peer-review acceptance (~320 tests) |
| `github-integration` | `test:github` | Live GitHub API smoke test — repo-scoped token validation and paginated fetch against `api.github.com` |
| `report-upstream-status` | — | Posts commit status to upstream PR (uses `UPSTREAM_STATUS_TOKEN` GitHub secret via `github-script`; token never logged) |

Store `UPSTREAM_STATUS_TOKEN` as a repository or organization secret in GitHub Settings → Secrets and variables → Actions.

### Local regression suite

Local regression suite (workflow structure, GitHub helpers, unit/integration coverage, test-script hygiene, fleet delivery checks, peer-review acceptance):

```bash
npm test
```

| Suite | Purpose |
|-------|---------|
| `validate-workflow.mjs` | Importable JSON structure, node wiring, secret hygiene |
| `collect-github-data.test.mjs` | GitHub record merge + pagination in workflow Code nodes |
| `github-collect-unit.test.mjs` | Unit tests for `validateGitHubToken`, `fetchGitHubPages`, `collectRecords` |
| `workflow-integration.test.mjs` | Token gate + mocked GitHub fetch + Claude prompt payload |
| `claude-summary.test.mjs` | Claude Sonnet 4 narrative generation (Build Claude Prompt, Claude API, Format Summary) |
| `delivery-channels.test.mjs` | Discord, Slack, and email payload + webhook delivery tests |
| `validate-github-token.mjs` | Pre-flight script: verify `GITHUB_TOKEN` repo read access |
| `test-scripts-acceptance.test.mjs` | Static checks on all test scripts |
| `delivery-verification.test.mjs` | Fleet handoff gates (branch diff, PROOF, npm test wiring) |
| `peer-review-acceptance.test.mjs` | Bounty #5 acceptance criteria regression |

CI mirror (attribution scan, `git diff --check`, ordered summary lines for fleet delivery gates):

```bash
npm run test:ci
jq empty weekly-dev-summary.json
```

Validate GitHub token permissions before enabling the workflow:

```bash
npm run test:validate-token
```

Optional live GitHub API check (CI sets `UPSTREAM_STATUS_TOKEN`; local runs may use `GITHUB_TOKEN` or `gh auth token`):

```bash
UPSTREAM_STATUS_TOKEN=<token> npm run test:github
# or locally:
GITHUB_TOKEN=<token> npm run test:github
```

Optional full n8n execution + screenshot regeneration (requires `n8n` CLI and `GITHUB_TOKEN`):

```bash
npm run test:e2e
```

The `tests/test-scripts-acceptance.test.mjs` step statically validates all test scripts (shebang, secret hygiene, package.json wiring) before delivery verification runs.

## Test evidence

See `assets/n8n-execution-screenshot.png` for a successful import and execution on n8n v1.82.
