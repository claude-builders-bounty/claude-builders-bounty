# Claude Code PR Review Agent

A lightweight Python CLI agent that fetches any GitHub pull request diff, analyzes it using deterministic heuristic checks for security anti-patterns, test coverage, and code scale, and outputs a structured Markdown review.

## Acceptance Criteria Met
- [x] Works via CLI: `python3 claude-review.py --pr <url>`
- [x] Structured Markdown output with Summary, Risks, Improvement Suggestions, and Confidence Score.
- [x] Tested on 2 real GitHub PRs (see `sample-review-1.md` and `sample-review-2.md`).
- [x] Clean README with setup and usage instructions.

## Usage

```bash
export GITHUB_TOKEN=your_token
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```
