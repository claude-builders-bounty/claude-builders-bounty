# claude-review — structured PR review from a diff

A CLI and GitHub Action that reads a pull request and returns a structured Markdown review:
**summary, risks, improvement suggestions, and a confidence score**.

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Works with **zero API key** — the analysis is a deterministic pass over the diff, so it is fast,
free, and repeatable. There is no model call to pay for and no prompt to drift.

## Output shape

```markdown
## Review: feat(api): add pagination to /users

`octocat` · 4 file(s) · +128/-31 (159) · confidence **Medium**

### Summary

This PR adds functionality across 4 files (+128/-31). It concentrates on src/api, test/api.
The description explains the intent.

### Risks

- **No test files changed** — the new behaviour is unverified by the diff.
- **Auth surface touched** — check the unauthenticated path, not just the happy flow.

### Improvement suggestions

- Add at least one test that fails before this change and passes after.

### Confidence

**Medium** — some risk signals or missing tests/description; a normal careful review.
```

## Install

Needs Node 20+. No dependencies.

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
cd claude-builders-bounty/agents/pr-reviewer
node bin/claude-review.mjs --help
```

Optional: `ln -s "$PWD/bin/claude-review.mjs" /usr/local/bin/claude-review`.

Set `GITHUB_TOKEN` to raise the API rate limit (60/hour unauthenticated, 5000/hour with a token).

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123          # print to stdout
claude-review --pr <url> --out review.md                           # write to a file
claude-review --repo owner/repo --number 123 --json                # machine-readable
claude-review --pr <url> --post                                    # comment via the gh CLI
claude-review --pr <url> --fail-on high                            # CI gate
claude-review --pr <url> --no-footer                               # no attribution line
```

`--fail-on low|medium|high` exits 1 when confidence is at or below that level — use it to block a
risky PR behind a required check.

## As a GitHub Action

```yaml
- uses: actions/checkout@v4
- uses: claude-builders-bounty/claude-builders-bounty/agents/pr-reviewer@main
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    fail-on: low
```

Or copy `.github/workflows/claude-review.yml` for a standalone workflow that posts a **sticky**
comment — it updates its own previous comment instead of stacking a new one on every push.

Required permissions: `contents: read`, `pull-requests: write`.

## What it flags

| Risk | Trigger |
|---|---|
| Schema/data change | a `migrations/`, `*.sql`, `schema.` or `prisma/` path |
| Lockfile committed | `package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`, … |
| CI workflow change | anything under `.github/workflows/` |
| Auth surface touched | auth/login/session/oauth/jwt/permission/rbac in the path |
| Hardcoded credential | a long literal assigned to `*_key` / `secret` / `token` / `password`, and not from the environment |
| No tests changed | source changed, no test path touched |
| Large / very large diff | ≥400 / ≥1000 changed lines |
| Empty catch block | an added `catch (e) {}` |
| Type escape hatch | an added `@ts-ignore`, `as any`, `eslint-disable` |
| File deletion, binary change, draft PR | status / patch inspection |

Confidence is not sentiment: it falls with size, missing tests and a missing description, and
rises when the diff is small, tested and described. It is a **triage signal**, not a verdict.

## Limits — stated honestly

- It reads the **diff**, not the repository. A function used wrongly elsewhere still looks fine here.
- It cannot run the tests, so "has tests" is not "passes tests".
- Heuristics will occasionally misfire: a lockfile bump with a real transitive regression still
  gets one line, not a deep analysis.
- It is a reviewer's assistant. It does not replace a human read, and the footer says so.

## Tests

```bash
node --test test/analyze.test.mjs
```

11 tests over the analysis core: every risk trigger, the environment-variable exemption, the
large-diff confidence drop, draft/deletion/binary handling, a `null` patch, and both markdown
paths (with and without findings).

`samples/` holds two real runs against live PRs.
