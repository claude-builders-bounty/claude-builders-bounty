---
name: pr-review-agent
description: Review a GitHub pull request and produce structured Markdown output with summary, risks, suggestions, and confidence score.
---

# PR Review Agent

Analyze a GitHub PR diff and return a structured Markdown review.

## Usage

```bash
# Review a PR by URL
/review-pr https://github.com/owner/repo/pull/123

# Review with explicit repo format
/review-pr owner/repo/123
```

## Prerequisites

- `GITHUB_TOKEN` — GitHub personal access token (public repo access)
- `ANTHROPIC_API_KEY` — Optional, enables Claude-powered analysis

Without `ANTHROPIC_API_KEY`, the agent uses built-in heuristic analysis
(pattern matching, diff size assessment).

## Output Structure

The review includes:
- **Summary of Changes** — 2-3 sentence overview
- **Identified Risks** — List of potential issues
- **Improvement Suggestions** — Actionable recommendations
- **Confidence Score** — Low / Medium / High

## Files

- `skills/pr-review-agent/review.py` — Main agent script
- `skills/pr-review-agent/skill.json` — Skill manifest
- `.github/workflows/pr-review.yml` — GitHub Action workflow
