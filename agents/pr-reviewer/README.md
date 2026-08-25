# claude-review — structured PR review agent

CLI and GitHub Action that fetch a pull request diff and emit a structured Markdown review.

## Setup

```bash
pip install --user anthropic  # optional; heuristic fallback works without API key
export ANTHROPIC_API_KEY=sk-ant-...  # optional, enables Claude-powered review
chmod +x claude_review.py
```

Requires [GitHub CLI](https://cli.github.com/) authenticated (`gh auth login`).

## Usage

```bash
./claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3863
./claude_review.py --pr https://github.com/owner/repo/pull/123 -o review.md
```

## Output format

- Summary (2–3 sentences)
- Identified risks (bullet list)
- Improvement suggestions (bullet list)
- Confidence score: Low / Medium / High

## GitHub Action

See `.github/workflows/claude-review.yml`. Trigger manually with a PR URL input, or on `pull_request` events.

## Sample runs

Included under `samples/` from two real PRs in this bounty repo (generated with heuristic mode, no API key).
