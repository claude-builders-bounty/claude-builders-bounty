# Test Provenance

## Real PR reviews (the outputs in this directory)

Both reviews were produced by running the CLI against live GitHub PRs on
2026-10-14:

| PR | Model | Endpoint | Result |
|---|---|---|---|
| [github-linguist/linguist#8272](https://github.com/github-linguist/linguist/pull/8272) | `nemotron-3.5-lightning-free` | local OpenAI-compatible router (`http://localhost:18892/v1`) | `review-8272.md` — rc=0, all four sections present |
| [claude-builders-bounty/claude-builders-bounty#4840](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4840) | `nemotron-3.5-lightning-free` | same router | `review-4840.md` — rc=0, all four sections present |

The diffs were fetched live via the `gh` CLI (the tool's primary path); no
diff content was hand-written or edited. The outputs in this directory are
the verbatim CLI stdout.

Notable sanity check: the review of PR #4840 correctly identified a real risk
in that PR's awk-based section-splice logic and its keyword-classification
fallbacks — evidence the model is analyzing the actual diff, not echoing the
prompt.

## Contract tests

- **Valid PR URL** → review printed, rc=0
- **Non-PR URL** (`https://example.com/notapr`) → clean error, rc=1
- **LLM output missing a required section** → warning printed, rc=1
  (verified against a stub endpoint that omits sections)
- **Missing diff** (private repo, no `GITHUB_TOKEN`) → clean error naming the
  likely cause

## Stub server

`stub_server.py` (not part of the deliverable, kept for reproduction) served a
fixed review on `127.0.0.1:18999` to exercise the validation path without
burning free-tier quota.
