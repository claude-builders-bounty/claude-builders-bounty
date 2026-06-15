# claude-review — PR Agent

A Claude Code sub-agent that reviews a GitHub Pull Request and returns a structured Markdown report.

**Bounty:** [#4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Install

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY=sk-ant-***
export GITHUB_TOKEN=ghp_***        # optional, for private repos

# 2. Run anywhere — no pip install needed (pure Python stdlib)
```

## Usage

```bash
python pr_agent.py --pr https://github.com/owner/repo/pull/123
```

## Example

```bash
python pr_agent.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2808
```

Output:

```markdown
# Code Review

## Summary
(2-3 sentences about the PR)

## Identified Risks
- ...

## Improvement Suggestions
- ...

## Confidence Score
**High**
```

## Requirements

- Python 3.10+
- `ANTHROPIC_API_KEY` env var
- Network access to `api.github.com` + `api.anthropic.com`
