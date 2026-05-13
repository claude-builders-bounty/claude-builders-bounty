# Claude PR Review Agent

A small Claude Code sub-agent for bounty #4. It reviews a GitHub pull request diff and prints a structured Markdown review comment.

## Install

```bash
chmod +x claude-review/bin/claude-review
sudo ln -sf "$PWD/claude-review/bin/claude-review" /usr/local/bin/claude-review
```

If you do not want a global symlink, run it directly:

```bash
./claude-review/bin/claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Output format:

```markdown
## Summary
...

## Identified risks
- ...

## Improvement suggestions
- ...

## Confidence
Medium — ...
```

## How it works

1. Parses the GitHub PR URL.
2. Fetches PR metadata and the unified diff from the GitHub API.
3. Builds a reviewer prompt for Claude Code.
4. Calls `claude -p` when Claude Code is installed.
5. Falls back to a deterministic heuristic reviewer if Claude Code is unavailable, which keeps CI and demos reproducible.

Set `GITHUB_TOKEN` if you need higher API rate limits or access to private repositories.

## GitHub Action option

This repo also includes `.github/workflows/claude-review.yml`. Add `ANTHROPIC_API_KEY` or a runner with Claude Code available if you want full Claude-powered reviews. Without Claude Code, the workflow still produces the same structured heuristic review.

## Tested examples

The `sample-outputs/` directory contains two real public PR runs:

- `openstreetmap-ng-261.md`
- `claude-builders-1168.md`

Regenerate them with:

```bash
./claude-review/bin/claude-review --pr https://github.com/openstreetmap-ng/openstreetmap-ng/pull/261 > claude-review/sample-outputs/openstreetmap-ng-261.md
./claude-review/bin/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1168 > claude-review/sample-outputs/claude-builders-1168.md
```
