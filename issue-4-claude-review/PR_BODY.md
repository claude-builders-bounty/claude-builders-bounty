## Summary

This submission adds a Claude Code PR reviewer agent package under `issue-4-claude-review/`.

It includes:
- a CLI entrypoint: `claude-review --pr https://github.com/owner/repo/pull/123`
- a dedicated PR reviewer sub-agent prompt
- structured Markdown output validation
- a GitHub Action example
- two real sample review outputs captured from public GitHub pull requests
- setup and usage documentation

## Acceptance Checklist

- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action example included in `examples/github-action.yml`
- [x] Structured Markdown output with:
  - [x] Summary
  - [x] Identified Risks
  - [x] Improvement Suggestions
  - [x] Confidence: Low / Medium / High
- [x] Tested on at least 2 real GitHub PRs
- [x] README with setup and usage instructions

## Real Sample Outputs

- `sample-outputs/openai-openai-node-pr-1867.md`
- `sample-outputs/claude-builders-bounty-pr-25.md`

## Validation

```bash
node --test
```

Passed locally: 4 tests, 0 failures.

## Notes

- The CLI package is self-contained under `issue-4-claude-review/` so it does not disturb the bounty board repo root.
- The sample outputs are committed as Markdown artifacts for easy maintainer review.
