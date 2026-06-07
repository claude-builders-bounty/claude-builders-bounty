# Proof for Bounty #4

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Acceptance mapping

- CLI works with `claude-review --pr https://github.com/owner/repo/pull/123`:
  - Implemented in `bin/claude-review.mjs`
  - Exposed through `package.json` bin as `claude-review`
- Claude Code sub-agent:
  - Added `.claude/agents/claude-pr-reviewer.md`
- GitHub Action workflow example:
  - Added `examples/github-action.yml`
- Structured Markdown output:
  - `## Summary of changes`
  - `## Identified risks`
  - `## Improvement suggestions`
  - `## Confidence score: Low|Medium|High`
- Tested on 2 real GitHub PRs:
  - `samples/react-32781.md`
  - `samples/node-58362.md`
- README with setup and usage:
  - `README.md`

## Verification commands

```bash
cd claude-review-agent
npm run sample:react
npm run sample:node
npm test
```

Result:

```text
verified 2 sample reviews
```

## Safety

- No secrets or account credentials are committed.
- `GITHUB_TOKEN` is optional for CLI use and only needed for rate limits or private PRs.
- The CLI prints or writes Markdown; it does not post comments automatically.
