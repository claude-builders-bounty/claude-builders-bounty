# Test Notes

## Documentation Basis

Claude Code sub-agents are Markdown files with YAML frontmatter. Project
sub-agents live under `.claude/agents/`.

Reference: https://code.claude.com/docs/en/sub-agents

## Commands Run

```bash
node --check bin/claude-review.mjs
node --check test/claude-review.test.mjs
npm test
```

Result:

```text
claude-review offline CLI smoke test passed
```

The exact CLI command name was also tested through a temporary npm install:

```bash
npm install --prefix "$TEMP/claude-review-cli" .
export GITHUB_TOKEN=...
PATH="$TEMP/claude-review-cli/node_modules/.bin:$PATH" \
  claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1359 --engine local
```

The token was used only to avoid public GitHub API rate limits during testing.

Claude Code sub-agent mode was also tested:

```bash
claude-review \
  --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1359 \
  --engine claude \
  --max-diff-chars 8000 \
  --max-budget-usd 0.25
```

Result: the bundled `pr-reviewer` sub-agent returned the required Markdown
sections: summary, identified risks, improvement suggestions, and confidence
score.

The default command now uses `--engine auto`, which attempts the Claude Code
sub-agent first and falls back to deterministic local output if Claude is not
available.

## Real PR Samples

Sample outputs were generated from two real GitHub PRs:

- https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1359
- https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1360

The outputs are committed in `samples/`.
