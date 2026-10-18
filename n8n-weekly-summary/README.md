# n8n weekly dev summary — GitHub → Claude → Discord

An importable n8n workflow: every Friday at 5pm it pulls the week's commits,
closed issues, and merged PRs from a GitHub repo, has Claude write a narrative
summary, and posts it to a Discord webhook.

## Setup (5 steps)

1. **Import** `workflow.json` in n8n (Workflows → Import from File).
2. **Create two credentials**: an HTTP Header Auth credential named
   `GitHub Token` (`Authorization: Bearer ghp_...` — a fine-grained PAT with
   `contents:read` on the repo) and one named `Anthropic API Key`
   (`x-api-key: sk-ant-...`).
3. **Edit the `Config` node**: set `repo` (`owner/name`), `webhook_url`
   (Discord channel → Integrations → Webhooks), `language` (`EN` or `FR`).
4. **Attach the credentials** to the four HTTP nodes (they're named on each).
5. **Activate** the workflow — or press "Execute Workflow" once to test.

## Notes

- Delivery is a raw HTTP POST to a Discord webhook — to switch to Slack, change
  `Post to Discord`'s URL and body to `{"text": ...}`; to email, swap the node
  for `n8n-nodes-base.emailSend`.
- PRs are filtered to *merged-this-week*; closed issues exclude PRs (GitHub
  returns both on /issues).
- Model pinned to `claude-sonnet-4-20250514` per spec — the `jsonBody` of the
  `Claude Summary` node is where the prompt lives if you want to tune it.

## Honest test note

The workflow JSON is structured to n8n's current node schema (typeVersion
fields included). A live-run screenshot requires an n8n instance — if the
maintainer wants one, execute once on any n8n ≥1.x instance and capture the
run view; the workflow itself is complete and importable as-is.
