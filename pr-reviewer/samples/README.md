# Sample outputs

Two real reviews produced by `claude-review` against public pull requests:

| File | Pull request |
|------|--------------|
| `sample-1-psf-requests-6767.md` | https://github.com/psf/requests/pull/6767 |
| `sample-2-pallets-click-2800.md` | https://github.com/pallets/click/pull/2800 |

Command used:

```bash
CLAUDE_REVIEW_MODEL=claude-sonnet-5-5 CLAUDE_REVIEW_EFFORT=medium \
  ./pr-reviewer/claude-review --pr https://github.com/psf/requests/pull/6767 --output pr-reviewer/samples/sample-1-psf-requests-6767.md
CLAUDE_REVIEW_MODEL=claude-sonnet-5-5 CLAUDE_REVIEW_EFFORT=medium \
  ./pr-reviewer/claude-review --pr https://github.com/pallets/click/pull/2800 --output pr-reviewer/samples/sample-2-pallets-click-2800.md
```

(`tests/fixtures/mock_review.md` is a test fixture, not a real review.)
