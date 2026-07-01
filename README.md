# Claude Builders Bounty Submissions

## Bounty #4: `claude-review` structured PR review agent

This submission adds a CLI agent at `bin/claude-review`.

It accepts a pull request URL or local diff file and prints a structured Markdown review comment with:

- Summary
- Potential issues
- Suggested tests
- Reviewer questions

### Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
bin/claude-review --diff-file tests/fixtures/sample.diff
```
