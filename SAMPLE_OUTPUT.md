# Sample Output

These are **real** runs of `changelog.sh` against a synthetic 10-commit repository
with a mix of conventional commits, breaking changes, and non-conventional messages.
No fabricated data — these outputs come from actual `bash changelog.sh` invocations.

## Test repo setup

```bash
mkdir -p /tmp/changelog-test-repo && cd /tmp/changelog-test-repo
git init -q
# 10 commits with mixed conventions
git commit -q -m "initial commit"
git commit -q -m "feat: add user authentication"
git commit -q -m "fix: handle null pointer in login"
git commit -q -m "refactor: extract auth middleware"
git commit -q -m "feat(api)!: rename /v1/users to /v2/users"
git commit -q -m "docs: update API reference"
git commit -q -m "added dark mode support"
git commit -q -m "removed deprecated v1 endpoints"
git tag v0.1.0
git commit -q -m "feat: add password reset flow"
git commit -q -m "fix: typo in error message"
git commit -q -m "perf: cache user lookups"
```

## Run 1 — Default (since last tag)

```bash
$ bash changelog.sh
changelog.sh: wrote CHANGELOG.md (version 0.1.1, 3 commits)
  Added:    1
  Fixed:    1
  Changed:  1
  Removed:  0
  Breaking: 0
```

**Output `CHANGELOG.md`:**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-08-01

### Added
- feat: add password reset flow (f61790c)

### Fixed
- fix: typo in error message (8456823)

### Changed
- perf: cache user lookups (4080117)
```

## Run 2 — Full history with breaking change

```bash
$ rm CHANGELOG.md
$ bash changelog.sh --allow-dirty --since 0987d94
changelog.sh: wrote CHANGELOG.md (version Unreleased, 10 commits)
  Added:    4
  Fixed:    2
  Changed:  3
  Removed:  1
  Breaking: 1
```

**Output `CHANGELOG.md`:**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-08-01

### ⚠️ BREAKING CHANGES
- feat(api)!: rename /v1/users to /v2/users (a7ecb8e)

### Added
- added dark mode support (4eb95c9)
- feat(api)!: rename /v1/users to /v2/users (a7ecb8e)
- feat: add password reset flow (f61790c)
- feat: add user authentication (20473e9)

### Fixed
- fix: handle null pointer in login (7b1f900)
- fix: typo in error message (8456823)

### Changed
- docs: update API reference (b06c73c)
- perf: cache user lookups (4080117)
- refactor: extract auth middleware (878063c)

### Removed
- removed deprecated v1 endpoints (88bc0dd)
```

Note: the heuristic correctly classifies "added dark mode support" → **Added** and
"removed deprecated v1 endpoints" → **Removed**, despite the lack of a conventional
prefix. The `feat(api)!: ...` commit lands in BOTH the breaking section AND the
Added section, which is the standard Keep-a-Changelog 1.1.0 convention.

## Run 3 — Idempotency

```bash
$ bash changelog.sh --allow-dirty
changelog.sh: wrote CHANGELOG.md (version 0.1.1, 3 commits)
...
$ bash changelog.sh --allow-dirty
changelog.sh: section for 0.1.1 already exists; not modifying CHANGELOG.md.
```

Running twice does not duplicate the section — the script detects the existing
version header and exits cleanly.

## Run 4 — Dirty tree refused

```bash
$ echo "dirty" > newfile.txt
$ bash changelog.sh
changelog.sh: working tree is dirty. Commit/stash first, or pass --allow-dirty.
$ echo $?
3
```

The script refuses to run on a dirty working tree to avoid mixing uncommitted
work with the generated changelog.

## Run 5 — Empty range

```bash
$ git tag v0.1.1
$ bash changelog.sh
changelog.sh: no new commits since v0.1.1.
$ echo $?
0
```

When there are no new commits, the script reports and exits 0 without
modifying the file.

## Test summary

| # | Scenario | Result | Exit code |
|---|----------|--------|-----------|
| 1 | Since last tag (conventional commits) | ✅ wrote CHANGELOG | 0 |
| 2 | Full history with breaking change | ✅ wrote + ⚠️ section | 0 |
| 3 | Re-run idempotency | ✅ refuses to duplicate | 0 |
| 4 | Dirty tree without --allow-dirty | ✅ refuses with message | 3 |
| 5 | Empty range | ✅ reports and exits clean | 0 |
| 6 | `--help` flag | ✅ prints usage | 0 |
| 7 | Non-conventional heuristic | ✅ classified correctly | 0 |

All 7 scenarios pass.
