# Approval Packet

This packet defines the next approval-gated steps for issue #5. It does not grant approval by itself.

## Approval 1: Real Endpoint Evidence

Required approval text:

```text
I approve running the real endpoint evidence workflow for issue #5 with environment-provided Anthropic and Slack credentials.
```

This approval covers only:

- validating the local environment variables
- executing `validate-real-execution.mjs` against real public GitHub, Anthropic, and Slack endpoints
- writing sanitized evidence to `evidence/real-execution-result.json`
- retaining a temporary local n8n user folder only long enough to capture `evidence/real-n8n-execution-ui.png`

This approval does not cover:

- posting `/opire try`
- pushing a branch or opening a PR
- creating accounts, accepting terms, or entering payment details
- using Binance, Lightspeed, trading credentials, or live funds

## Credential Handling

Provide credentials only as environment variables in the local shell:

```bash
export ANTHROPIC_API_KEY="<approved Anthropic API key>"
export SLACK_WEBHOOK_URL="<approved Slack incoming webhook URL>"
```

Do not paste credentials into source files, Markdown files, screenshots, PR text, issue comments, shell history shared publicly, or committed evidence.

## Commands After Approval 1

```bash
node submissions/aviranchigoda/validate-real-execution.mjs --check-env-only
node submissions/aviranchigoda/validate-real-execution.mjs
```

Expected evidence:

- `submissions/aviranchigoda/evidence/real-execution-result.json`
- `submissions/aviranchigoda/evidence/real-n8n-execution-ui.png`

Final strict checks:

```bash
node submissions/aviranchigoda/check-acceptance.mjs --require-real-evidence
node submissions/aviranchigoda/pre-submit-audit.mjs --require-real-evidence
```

Both strict checks must pass before public submission is requested.

## Approval 2: Public Claim And PR

Required approval text after Approval 1 evidence passes:

```text
I approve commenting /opire try on issue #5 and opening the prepared public PR for the issue #5 submission.
```

Use `PUBLIC_SUBMISSION_DRAFT.md` for the exact claim comment, PR title, PR body source, target branch metadata, and stop conditions.

## Stop Conditions

- Stop if environment preflight fails.
- Stop if real execution fails or produces unsanitized evidence.
- Stop if either strict check fails.
- Stop if any secret-like token appears in `submissions/aviranchigoda/`.
- Stop before any public action unless Approval 2 is explicit.
- Stop before Phase 2 until the bounty payout is awarded and verified.
