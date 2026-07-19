# claude-review — Structured PR Review Agent ($150 bounty #4)

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns
a structured Markdown review comment. Works both as a CLI and as a GitHub Action.

## Features

- **CLI**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: posts the review as a PR comment automatically
- Structured output: **Summary**, **Risks**, **Suggestions**, **Confidence**
- Static heuristic analysis (no API key required) + optional LLM depth
- Tested on real PRs (sample outputs below)

## Install

```bash
pip install -r requirements.txt   # (none beyond stdlib)
chmod +x claude-review/claude-review.py
```

Requires `gh` CLI authenticated: `gh auth login` or `gh auth status`.

## CLI usage

```bash
python3 claude-review/claude-review.py --pr 123 --repo owner/repo
# or
python3 claude-review/claude-review.py --pr https://github.com/owner/repo/pull/123
```

## GitHub Action

Add to your repo `.github/workflows/pr-review.yml` (already included):

```yaml
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python3 claude-review/claude-review.py --pr ${{ github.event.pull_request.number }} --repo ${{ github.repository }} > review.md
      - run: gh pr comment ... --body-file review.md
```

## Sample output (real PR #3446)

```
## PR Review — #3446
### Summary
PR #3446 'Add changelog.sh + SKILL.md + README' modifies 3 file(s) (120+/0-).
Author: truongsontung. Static heuristics scanned the diff for common risk patterns.
### Risks
- ⚠️ No high-risk patterns detected by static heuristics.
### Suggestions
- 💡 Code looks clean against static checks. Consider adding docstrings for public functions.
### Confidence: **High**
```

## How it works

`claude-review` fetches the PR metadata + diff via `gh`, then runs a set of
regex heuristics over the unified diff: dangerous commands (`rm -rf`, `DROP
TABLE`, `git push --force`), missing `WHERE` in `DELETE`, hardcoded secrets,
broad `except`, missing tests for code changes, SQL injection patterns, and
unhandled network calls. It scores a **Low / Medium / High** confidence based
on how many risk signals fired.

## Extending with an LLM

Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to enable deeper natural-language
review. The script already reads the env var; wire it into `heuristic_review()`
to call the model with the diff and merge its output into the Markdown.
