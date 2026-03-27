## Summary

Adds a `claude-review` CLI that reviews a GitHub pull request URL and outputs a structured Markdown review.

### What’s included
- `claude-review --pr <url>` CLI
- Structured output with:
  - Summary
  - Risks
  - Improvement Suggestions
  - Confidence
- README with setup / usage
- Two real sample outputs:
  - `openai/openai-python#2345`
  - `openai/openai-node#1798`
- Basic tests + smoke integration check

## How to test

```bash
cd pr-reviewer
npm install
npm test
./tests/integration-smoke.sh
node src/cli.js --pr https://github.com/openai/openai-python/pull/2345
```

## Notes
- This submission implements the CLI path from the issue requirements.
- It uses `gh` to fetch PR metadata and diff, then generates a structured Markdown review.
