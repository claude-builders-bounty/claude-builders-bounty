# Sample outputs

Live sample reviews of two real public PRs have **not** been generated yet: the environment this was built in had no network or API access, and outputs are never fabricated.

To generate them:

```bash
./pr-reviewer/claude-review --pr https://github.com/OWNER/REPO/pull/N --output pr-reviewer/samples/sample-1.md
./pr-reviewer/claude-review --pr https://github.com/OWNER/REPO/pull/M --output pr-reviewer/samples/sample-2.md
```

(`tests/fixtures/mock_review.md` is a test fixture, not a real review.)
