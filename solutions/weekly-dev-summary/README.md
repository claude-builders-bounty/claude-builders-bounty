# Weekly GitHub development summary

**Started:** 2026-09-26

An importable n8n workflow that reports a repository's activity over the previous seven days: commits, closed issues (excluding pull requests), and merged pull requests. It uses public GitHub REST endpoints and the Anthropic Messages API to write the summary in English or French. Discord and Slack incoming webhooks are supported.

## Setup and run

1. Open an n8n instance with HTTP Request, Code, Merge, and Schedule Trigger nodes. Local verification used n8n 2.40.7 and Node.js 26.9.0; no host-shell node or Claude Code installation is required.
2. Import `solutions/weekly-dev-summary/workflow.json`. In **Call Claude API**, select your existing [Anthropic credential](https://docs.n8n.io/integrations/builtin/credentials/anthropic). n8n supplies the API key; the workflow export contains no key or environment-variable lookup.
3. In **Set Options**, set `repo` to `owner/repository`, choose `en` or `fr`, set `destinationType` to `discord` or `slack`, and paste the matching incoming webhook URL. Keep `sendDelivery` false while reviewing the first run.
4. Run **Run Manually** and review the generated summary and delivery payload. Live runs call Anthropic's billed API; a Claude Code subscription is not an API credential. The local verification command below makes no live provider call.
5. When ready, set `sendDelivery` true and activate the workflow. It runs Friday at 17:00 UTC; Discord uses `content`, Slack uses `text`.

The starter webhook is a placeholder and delivery is off by default. GitHub requests follow the API's `Link` headers, with one second between pages. Commits and issues use the weekly API filters; closed PRs are ordered by update time and paging stops after crossing the weekly start. Counts include every matching record, while the prompt contains at most 20 highlights per category and explicitly reports how many details it omits. API errors, rate limits, or incomplete pagination stop the workflow before a summary is generated. GitHub's unauthenticated API rate limit applies.

The bounty originally specified `claude-sonnet-4-20250514`. Anthropic retired that model on 2026-06-15 and recommends `claude-sonnet-4-6`; this workflow uses that supported successor and does not claim to run the retired model. See [Anthropic's model deprecation notice](https://platform.claude.com/docs/en/about-claude/model-deprecations).

The **Call Claude API** node posts to `/v1/messages` with `anthropic-version: 2023-06-01`, a 1,024-token output budget, and one user message. The response validator joins only text blocks from a complete assistant message. HTTP errors, empty text, incomplete/refused responses, and text over the 1,800-character delivery limit stop the workflow; they are not silently retried or sent. See [Messages API usage](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) and [stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).

## Local checks

```sh
cd solutions/weekly-dev-summary
npm test
npm run build:workflow
```

`npm test` validates multi-page activity (including more than 100 records), date filtering, exclusion of closed-but-unmerged PRs, completeness checks, explicit highlight sampling, webhook host checks, and default-off delivery. The workflow JSON is self-contained; the small build script embeds the reviewed Code node sources into it.

For real n8n pagination and HTTP mapping checks without inference or external delivery, set `N8N_BIN` to your installed n8n executable and run `npm run verify:pagination`. The verifier imports into a temporary local data folder, serves synthetic GitHub pages and Messages responses on loopback, and checks 135 weekly entries in each category plus successful text extraction, HTTP 429, empty content, and truncated responses. The test copy removes the Anthropic credential reference and targets loopback; the export remains configured for an n8n-managed Anthropic credential. Its compact result is saved in `evidence/pagination-verification.json`; it verifies request/response mapping, not live Anthropic authentication or generation.

To render a shareable, explicitly synthetic execution receipt from that result, run `npm run render:verification-report`. The report is `evidence/local-n8n-verification-report.html`; its screenshot is `output/playwright/local-n8n-verification.png`. This is a rendered receipt of an actual isolated n8n CLI run, not the n8n editor UI or a live Anthropic call.

The earlier real Claude Code execution and screenshot are preserved in `evidence/cli-execution.md` as historical evidence of the September 25 CLI version. They are not a live execution receipt for the current Messages API workflow. No live API request was made while validating this revision.
