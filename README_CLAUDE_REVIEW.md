# claude-review — AI-Powered PR Review Agent

> 🔍 Bounty #4 ($150): PR reviewer with structured output

`claude-review` is a Python CLI that fetches a GitHub PR's unified diff and
generates a structured review with **Summary**, **Risks**, **Suggestions**, and
a **Confidence score** (0-100). It tries Claude Code first, then the Anthropic
API, then falls back to a template.

## Quick Start

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.json
./claude-review --pr https://github.com/owner/repo/pull/123 --fallback   # no AI needed
```

## Prerequisites

| Backend | Requirement |
|---------|------------|
| Claude Code CLI | `claude` installed + `claude auth login` |
| Anthropic API | `ANTHROPIC_API_KEY` env var + `pip install anthropic` |
| Template fallback | Nothing — always works |

Also requires [GitHub CLI](https://cli.github.com/) (`gh`) for diff/metadata fetching.

## Usage

```
usage: claude-review [-h] --pr PR [--model MODEL] [--fallback]
                     [--output OUTPUT] [--timeout TIMEOUT] [--no-metadata]
```

## Output Format

```json
{
  "summary": "Concise 2-5 sentence summary of the PR...",
  "risks": ["Specific risk 1...", "Specific risk 2..."],
  "suggestions": ["Actionable improvement 1...", "Actionable improvement 2..."],
  "confidence": 78
}
```

## Sample Reviews

See `pr-reviews/` for sample outputs from real PRs:

| File | PR Reviewed |
|------|-------------|
| [`review-pr-2067.json`](pr-reviews/review-pr-2067.json) | #2067 — Add Claude PR review CLI agent |
| [`review-pr-2073.json`](pr-reviews/review-pr-2073.json) | #2073 — Add Hybrid AST/Kernel-level Security Hook |

## Architecture

```
User → claude-review --pr <URL>
         │
         ├─ gh pr diff   → fetch unified diff
         ├─ gh pr view   → fetch metadata (title, author, files)
         │
         ├─ Claude Code  → claude -p (if authenticated)
         ├─ Anthropic API → messages.create() (if API key set)
         └─ Template     → structured template (always available)
         │
         └─ JSON output  → summary, risks, suggestions, confidence
```

## Integration

- **GitHub Actions**: Run on PR open/sync, post review as comment
- **Git hooks**: Block merges below confidence threshold
- **Slack/Discord**: Pipe summary to team channel
- **Claude Code**: Register as an agent for `/review` commands
