# claude-review — Automated PR Reviewer

Analyzes a GitHub Pull Request and outputs a structured Markdown review.

## Usage

### Print review to stdout

```bash
./claude-review/claude-review.sh https://github.com/owner/repo/pull/123
```

### Post review as GitHub comment

```bash
export GH_TOKEN=ghp_xxx
./claude-review/claude-review.sh https://github.com/owner/repo/pull/123 --post
```

## Output Format

```markdown
## PR Review: Fix login flow

**Author:** @devuser | **+42 additions** / **-15 deletions** / **3 files**

### Summary
This PR by @devuser adds 42 and removes 15 lines across 3 file(s). Merging into `main` from `fix/login`.

### Risks
- Sensitive config files modified: .env.example — check for leaked secrets

### Improvement Suggestions
- No test files in this PR — consider adding tests

### Confidence: Medium
```

## Detection Rules

### Risks
| Signal | Threshold | Confidence Impact |
|--------|-----------|-------------------|
| Large PR | > 400 lines added | Low |
| Many files | > 20 files | Low |
| Delete-heavy | Deletions > additions and > 100 | — |
| Binary files | Any .png/.jpg/.zip/etc | — |
| Config/secrets | .env, credentials, private_key files | Low |
| DB migrations | Any migration file | — |
| Merge conflicts | Not mergeable | Low |

### Suggestions
| Signal | Trigger |
|--------|--------|
| No description | Body < 50 chars |
| No tests | No test files + > 30 lines added |
| Breaking change | “breaking”/“BC” in title/body |
| TODO/FIXME | Present in diff |

## Sample Output on Real PRs

### PR: claude-builders-bounty/claude-builders-bounty#3789

```
$ ./claude-review/claude-review.sh https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3789

## PR Review: feat: add CHANGELOG generation skill and bash script

**Author:** @maxim65651 | **+229 additions** / **0 deletions** / **2 files**

### Summary
This PR by @maxim65651 adds 229 and removes 0 lines across 2 file(s). Merging into `main` from `feat/changelog-skill`.

### Risks
None identified.

### Improvement Suggestions
- No test files in this PR — consider adding tests for new/changed logic

### Confidence: High
```

### PR: typeorm/typeorm#12738

```
$ ./claude-review/claude-review.sh https://github.com/typeorm/typeorm/pull/12738

## PR Review: fix: preserve data when changing column length (3357)

**Author:** @luckyseoul | **+198 additions** / **23 deletions** / **8 files**

### Summary
This PR by @luckyseoul adds 198 and removes 23 lines across 8 file(s), including database migrations. Merging into `main` from `fix/preserve-data-column-length`.

### Risks
- Database migration files changed — verify reversibility and test on staging first

### Improvement Suggestions
None suggested.

### Confidence: Medium
```

## Prerequisites

- `curl` and `jq` (available on most systems)
- `gh` CLI (only needed for `--post`)
- `GH_TOKEN` or `GITHUB_TOKEN` env var (only needed for `--post`)
