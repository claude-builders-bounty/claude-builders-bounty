# Claude Review Agent CLI

Small CLI tool that reviews GitHub PR diffs and outputs structured Markdown.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Output format

- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High

## Notes

This implementation uses GitHub API (`gh api`) to fetch PR files/patches and applies deterministic heuristic analysis to produce review output.
