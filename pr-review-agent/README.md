# pr-review-agent

A Claude Code sub-agent (CLI) that fetches a GitHub pull-request diff,
analyzes it with an LLM, and produces a structured Markdown review —
Summary, Risks, Suggestions, and a Confidence score. Optionally posts the
review as a PR comment.

## Setup (2 commands)

```bash
pip install --user .            # or: cp claude-review ~/.local/bin/ && chmod +x
export LLM_API_KEY=sk-...       # any OpenAI-compatible endpoint key
```

Configuration (environment variables):

| Variable | Default | Meaning |
|---|---|---|
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL (OpenRouter, Anthropic compat, local routers) |
| `LLM_API_KEY` | *(unset)* | API key; omit for local routers that substitute their own |
| `LLM_MODEL` | `anthropic/claude-sonnet-4` | Model id as the endpoint expects it |
| `GITHUB_TOKEN` | *(unset)* | Optional; raises rate limits, enables private repos, enables `--post` fallback |
| `MAX_DIFF_CHARS` | `60000` | Diff budget before truncation (truncation is disclosed in the prompt) |

## Usage

```bash
# print the review to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# post the review as a comment on the PR
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

The tool exits non-zero if the LLM output violates the required structure,
so CI can fail on a malformed review.

## GitHub Action

`.github/workflows/pr-review.yml` runs the same CLI on every PR:

```yaml
name: PR Review
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Review the PR
        env:
          LLM_BASE_URL: ${{ secrets.LLM_BASE_URL }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: ${{ secrets.LLM_MODEL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -fsSL https://raw.githubusercontent.com/<you>/pr-review-agent/main/claude-review \
            -o claude-review && chmod +x claude-review
          ./claude-review --pr "${{ github.event.pull_request.html_url }}" --post
```

## Output format

```markdown
## Summary
(2-3 sentences)

## Risks
(- [high|medium|low] bullets, or "- none identified")

## Suggestions
(- concrete bullets, or "- none")

**Confidence:** Low | Medium | High
```

## Tested on

Two real GitHub PRs, reviewed by a real model through a local
OpenAI-compatible router (see `examples/PROVENANCE.md`):

1. [github-linguist/linguist#8272](https://github.com/github-linguist/linguist/pull/8272) — `examples/review-8272.md`
2. [claude-builders-bounty/claude-builders-bounty#4840](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4840) — `examples/review-4840.md`

Contract tests also verified: clean failure on a non-PR URL, and a
non-zero exit when the LLM output omits a required section.

## Files

- `claude-review` — the CLI (Python 3, stdlib only)
- `SKILL.md` — Claude Code skill wrapper
- `.github/workflows/pr-review.yml` — GitHub Action
- `examples/` — real review outputs + provenance
