# Claude PR Review Agent

CLI agent for reviewing a GitHub pull request diff and returning a structured Markdown review comment.

## Usage

```bash
npm test
node bin/claude-review.js --diff tests/fixtures/sample-pr.diff
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

The CLI prints:

- summary of changes
- identified risks
- improvement suggestions
- confidence score

It uses deterministic local analysis and does not require an API key.

## Real PR Smoke Tests

The CLI was tested against these public GitHub pull requests:

- `https://github.com/vercel/next.js/pull/93553`
- `https://github.com/vercel/next.js/pull/93260`

The generated review comments are stored in:

- `samples/vercel-next-93553-review.md`
- `samples/vercel-next-93260-review.md`

## Validation

```bash
npm run check
```

This command runs unit tests, generates a fixture-based review, and verifies the diff with `git diff --check`.
