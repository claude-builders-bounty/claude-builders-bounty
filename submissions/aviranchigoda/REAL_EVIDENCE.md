# Real Endpoint Evidence Runbook

Use this only after explicit approval to run the workflow against real Anthropic
and Slack endpoints. Do not paste credentials into source files, screenshots, or
PR text.

## Required Environment

```bash
export ANTHROPIC_API_KEY="..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export N8N_REAL_EVIDENCE_USER_FOLDER="$(mktemp -d /tmp/n8n-weekly-summary-real-ui-XXXXXX)"
export N8N_KEEP_REAL_EVIDENCE_USER_FOLDER=true
```

Optional:

```bash
export GITHUB_OWNER="claude-builders-bounty"
export GITHUB_REPO="claude-builders-bounty"
export SUMMARY_LANGUAGE="EN"
export LOOKBACK_DAYS="7"
export SLACK_CHANNEL=""
```

## Run Real Execution

```bash
node submissions/aviranchigoda/validate-real-execution.mjs
```

Expected result:

- `evidence/real-execution-result.json` is written.
- The JSON reports `status: "passed"`, `executedWorkflow: true`,
  `usedRealAnthropicApi: true`, `usedRealSlackWebhook: true`, and
  `finalStatus: "delivered"`.
- The file does not include the Anthropic API key or Slack webhook URL.
- The runner refuses to write the evidence file if an approval-gated secret
  value is detected in the sanitized evidence payload.
- The generated import workflow file is written outside the n8n user folder and
  deleted automatically after import.

## Capture n8n UI Screenshot

Start n8n with the same user folder used for the real execution:

```bash
N8N_USER_FOLDER="$N8N_REAL_EVIDENCE_USER_FOLDER" \
N8N_SECURE_COOKIE=false \
N8N_PORT=5680 \
N8N_RUNNERS_BROKER_PORT=5681 \
npm exec --yes --package n8n@2.20.11 -- n8n start
```

Open `http://127.0.0.1:5680`, finish any local owner setup if prompted, open
the workflow's Executions tab, and capture the successful real execution as:

```text
submissions/aviranchigoda/evidence/real-n8n-execution-ui.png
```

The screenshot should show the successful n8n execution state, but it must not
show the Anthropic API key or Slack webhook URL.

After the screenshot is captured, remove the temporary n8n user folder unless
you still need it for local review:

```bash
rm -rf "$N8N_REAL_EVIDENCE_USER_FOLDER"
```

## Final Local Check

```bash
node submissions/aviranchigoda/check-acceptance.mjs --require-real-evidence
```

After the strict check passes, the remaining public actions are commenting
`/opire try` on issue #5 and opening the PR.
