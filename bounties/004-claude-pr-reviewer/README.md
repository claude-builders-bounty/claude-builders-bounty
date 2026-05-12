# Claude PR Review Agent

A Claude Code sub-agent that fetches a GitHub pull request diff, analyzes it with Claude, and returns a structured Markdown review with summary, risks, improvement suggestions, and a confidence score.

## Install (3 commands)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...          # optional — raises GitHub API rate limit
```

## Usage

**Review a GitHub PR by URL:**
```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

**Review a local diff file:**
```bash
python claude-review --diff changes.diff
```

**Review from stdin (e.g., in a git hook or pipe):**
```bash
git diff main...HEAD | python claude-review --stdin
```

## Sample output

```markdown
## Summary

This PR delivers a PreToolUse hook for Claude Code that intercepts dangerous Bash
commands before they execute, returning a structured JSON block decision to Claude…

## Identified Risks

- Regex bypasses via shell quoting: commands like `rm '-r' '-f' /tmp` are not caught…
- No blocking of `sudo rm -rf`: the sudo prefix is not considered…

## Improvement Suggestions

- Add nvme and vd device patterns to the dd regex…
- Document sudo non-coverage in the README…

## Confidence Score

**High** — diff is small (352 lines across 3 files), well-tested…
```

Full sample outputs: [`samples/pr-1059-review.md`](samples/pr-1059-review.md) and [`samples/anthropic-sdk-1508-review.md`](samples/anthropic-sdk-1508-review.md)

## Claude Code Agent

The agent definition lives at [`agent/pr-reviewer.md`](agent/pr-reviewer.md). To run it directly inside a Claude Code session, copy it to your agents directory:

```bash
cp agent/pr-reviewer.md ~/.claude/agents/pr-reviewer.md
```

Then in any Claude Code session:
```
Review this PR: https://github.com/owner/repo/pull/123
```
Claude Code will automatically invoke the `pr-reviewer` sub-agent.

## GitHub Action

Copy [`.github/workflows/pr-review.yml`](.github/workflows/pr-review.yml) to your repo and add `ANTHROPIC_API_KEY` to repository secrets. The action posts a review comment on every new or updated PR automatically.

## Architecture

```
claude-review (CLI)
  │
  ├── fetch PR metadata + diff via GitHub API (no gh CLI required)
  ├── truncate diff at 40,000 chars to control cost/latency
  └── call Anthropic Python SDK with agent/pr-reviewer.md as system prompt
        └── returns structured Markdown review
```

The agent prompt instructs Claude to be specific and grounded — no invented context, no fabricated file names, explicit handling of missing tests or truncated diffs.
