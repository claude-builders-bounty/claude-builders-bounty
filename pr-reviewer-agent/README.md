# pr-reviewer

A Claude Code agent that reviews a PR diff and returns a structured
Markdown comment: summary, risks, suggestions, confidence score.

## Setup

1. Copy `.claude/agents/pr-reviewer.md` into your project's
   `.claude/agents/` (or `~/.claude/agents/` for global use).
2. Put `claude-review` on your PATH (`chmod +x claude-review`).

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --diff /path/to/change.patch
```

The CLI fetches the diff (`gh pr diff` when authed, otherwise the PR's
`.patch` URL), appends it to the agent's instructions, and runs
`claude -p`. Without the `claude` CLI it prints the ready-to-paste
review prompt instead.

## Output format

```
## PR Review
### Summary        — 2–3 sentences, blast radius
### Risks          — severity-ordered, diff-grounded
### Suggestions    — actionable only
### Confidence     — Low / Medium / High + one-line justification
```

## Sample outputs

- `outputs/sample-1-claude-code-action-620.md` —
  anthropics/claude-code-action#620 (docs + manifest feature): the
  agent catches a misconfigured `redirect_url`, a placeholder webhook
  URL, and a weak `state` token.
- `outputs/sample-2-x402-429.md` —
  coinbase/x402#429 (metadata-only change): the agent correctly
  stays quiet and flags the single enum check worth doing.
