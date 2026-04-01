# Claude Code PR Reviewer — Sub-Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured comments.

## Setup

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

# Review a PR
python agent.py owner repo 123
```

## Output Format

The agent posts a structured review:
- **Summary** — what the PR does
- **Code Quality** — rating + feedback
- **Issues Found** — bugs, security, concerns
- **Suggestions** — improvements
- **Verdict** — APPROVE / REQUEST_CHANGES / COMMENT
- **Confidence** — High / Medium / Low

## Requirements

- Python 3.10+
- `anthropic` SDK
- `gh` CLI authenticated
