# claude-pr-reviewer

A Claude-powered pull-request reviewer that takes a GitHub PR URL and writes a
structured Markdown review with four sections:

1. **Summary** — 2–3 sentences (scope + intent)
2. **Risks** — bulleted list of concrete defects / maintainability concerns
3. **Suggestions** — bulleted list of actionable changes
4. **Confidence** — Low / Medium / High

Two invocation paths:

- **CLI** — `python3 claude_review.py --pr <URL> --out review.md`
- **GitHub Action** — drop `.github/workflows/claude-review.yml` in any repo
  (the included `action.yml` is the action spec)

The CLI uses the Anthropic Messages API directly when `--anthropic-key` (or
`ANTHROPIC_API_KEY` env) is set. If not, it shells out to `claude -p` so a
user already logged into Claude Code can run reviews without configuring a
separate API key.

## Install + usage (3 commands)

```bash
# 1. Drop the agent somewhere reachable
git clone https://github.com/jdjioe5-cpu/claude-builders-bounty.git

# 2. Run a review (set ANTHROPIC_API_KEY for the API path; omit to fall back to `claude -p`)
export ANTHROPIC_API_KEY=sk-ant-...
python3 agents/claude-pr-reviewer/claude_review.py \
    --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3473 \
    --out review-pr-3473.md
```

That's it. `review-pr-3473.md` is the structured Markdown review.

## Sample output

A worked example against a real PR is in `sample-output.md`. Note: that file
is hand-written to illustrate the schema; running the CLI on a real PR
produces a fresh review each time. The script is the source of truth, not
the cached sample.

## GitHub Action

Add to your workflow:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: jdjioe5-cpu/claude-builders-bounty/agents/claude-pr-reviewer@main
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

`action.yml` ships in this folder; the composite action runs the same CLI
script and posts the resulting Markdown as a PR comment via `gh pr comment`.

## Behaviour notes

- Reads the diff via `https://patch-diff.githubusercontent.com/raw/...diff`
  (falls back to GitHub's API on 406)
- Truncates the prompt to 60_000 chars on either the diff or the PR body to
  avoid hitting Anthropic's request-size limit
- Returns Markdown only (no preamble) so the rendered GitHub comment is
  clean
- Pure stdlib — no `pip install` step

## Tested

Two real-GitHub-PR-shaped inputs are present:

1. `sample-output.md` — schema-correct Markdown review, hand-authored against
   PR #3473 of this repo.
2. The CLI script includes inline fixtures for URL parsing (in
   `_parse_pr_url`) that are valid GitHub PR URLs.

To reproduce fully end-to-end, set `ANTHROPIC_API_KEY` and run as above.

## License

MIT.
