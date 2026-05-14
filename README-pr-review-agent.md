# claude-review

A Claude Code PR-review agent + CLI for the Opire bounty: **AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment**.

## Install in 2 commands

```bash
cp -R .claude ~/
install -m 755 claude-review /usr/local/bin/claude-review
```

Optional for live Claude output:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without an API key, `claude-review` still runs in deterministic fallback mode so reviewers can test the CLI and output format without secrets.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The output is a GitHub-ready Markdown review comment with:

- 2–3 sentence summary
- identified risks
- improvement suggestions
- confidence score: Low / Medium / High

## Files

- `.claude/agents/pr-reviewer.md` — Claude Code sub-agent prompt.
- `claude-review` — CLI wrapper that fetches PR metadata + diff and emits the structured comment.
- `samples/` — outputs from two real public GitHub PRs.

## Notes

The CLI uses public GitHub endpoints and does not require a GitHub token for public PRs. Set `ANTHROPIC_API_KEY` to call `claude-sonnet-4-20250514`; otherwise the local fallback makes a conservative review from diff metadata and common risk patterns.
