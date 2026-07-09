# claude-review — AI pull-request reviewer

Turn any GitHub PR into a structured Markdown review — **Summary · Risks ·
Suggestions · Confidence (Low/Medium/High)** — powered by the Claude API
(`claude-sonnet-4-20250514`). Use it from the CLI or as a GitHub Action that
auto-comments on every PR.

## Setup
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # required
export GITHUB_TOKEN=ghp_...              # optional: higher rate limits / private PRs
```

## CLI usage
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
python claude_review.py --pr <url> --output review.md
python claude_review.py --diff-file local.diff          # review a local diff
```

## GitHub Action (auto-review every PR)
Copy the bundled [`github/claude-review.yml`](github/claude-review.yml) into your
repo at `.github/workflows/claude-review.yml` and add an `ANTHROPIC_API_KEY`
repository secret. The action fetches
the PR diff, generates the review, and posts it as a PR comment on open/synchronize.

## Output format
```markdown
## PR Review — owner/repo#123
## Summary
<2-3 sentences>
## Risks
- <risk>
## Suggestions
- <suggestion>
## Confidence
Medium
```

The tool always emits exactly these four sections, and normalizes the confidence
to one of `Low` / `Medium` / `High` (defaulting to `Medium` if the model is unclear).

## Sample outputs (real PRs)
See [`samples/`](samples/) — reviews generated for two real public PRs.

## Offline / CI testing
`--stub-file FILE` uses the file's contents as the model output instead of calling
the API, so the formatting pipeline can be exercised deterministically. The bundled
`validate_review.py` uses this to verify the output contract with no API key.
