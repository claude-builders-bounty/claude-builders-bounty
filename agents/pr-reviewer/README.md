# pr-reviewer — structured PR reviews from the CLI or GitHub Actions

Takes a PR diff and returns a structured Markdown review:
**Summary · Risks · Suggestions · Confidence (Low/Medium/High)**.

## CLI
```bash
# requires `gh` (authenticated). Uses Claude when ANTHROPIC_API_KEY is set,
# otherwise a deterministic local analyzer — zero config.
export ANTHROPIC_API_KEY=sk-ant-...        # optional
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr owner/repo#123 --json
```

## GitHub Action
Copy [`.github/workflows/claude-review.yml`](.github/workflows/claude-review.yml) into your
repo and add an `ANTHROPIC_API_KEY` secret. Every PR gets a review comment automatically.

## Output shape
```markdown
# PR Review — [title](url)

## Summary
7 file(s) changed, +307 / -0 lines. Focus areas: ...

## Risks
- Possible hardcoded secret
- No test files changed

## Suggestions
- Add a focused test for the behaviour this PR changes.

## Confidence
**High** — heuristic based on PR size and detected patterns.
```

## Sample outputs
- [`examples/pr-5133.md`](examples/pr-5133.md) — a docs/tooling PR
- [`examples/pr-5134.md`](examples/pr-5134.md) — a hook + tests PR

## Files
`claude-review` (CLI) · `prompts/review.md` (Claude system prompt) ·
`.github/workflows/claude-review.yml` (Action).

## Notes
- Fetching uses the `gh` CLI; no tokens hardcoded.
- The local analyzer detects: hardcoded secrets, `eval/exec`, SQL concatenation, debug
  output, swallowed exceptions, destructive git, added TODO/FIXME, disabled tests, and
  missing tests — then scores a confidence level from diff size.
