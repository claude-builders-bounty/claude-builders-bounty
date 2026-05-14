# PR Review Sub-agent

A standalone code review tool that fetches a GitHub PR diff and produces a structured Markdown review using an LLM.

## Setup (2 commands)

```bash
pip install -r requirements.txt   # no external deps needed — pure Python stdlib
export GITHUB_TOKEN=ghp_xxx
```

## Usage

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output

- **Summary** — 2–3 sentence overview of the PR
- **Identified Risks** — bugs, regressions, edge cases, security concerns
- **Improvement Suggestions** — code quality, performance, readability
- **Confidence Score** — Low / Medium / High

## GitHub Action

The `.github/workflows/pr-review.yml` workflow auto-reviews every opened/synchronized PR. Add your `LLM_API_KEY` and `GITHUB_TOKEN` as repository secrets.

## Samples

See `sample-output-1.md` and `sample-output-2.md` for real PR reviews.
