# Structured Changelog Generator

A dependency-free changelog generator for Claude Code builders. It turns a repo's git history into a reviewable `CHANGELOG.md` with categories, scopes, breaking changes, pull request references, commit links, and authors.

## Setup in 3 steps

1. Copy `changelog.sh`, `tools/changelog_generator.py`, and `SKILL.md` into any git repository.
2. Run `bash changelog.sh --repo . --output CHANGELOG.md --version Unreleased`.
3. Review the generated `CHANGELOG.md` and commit it with your release.

## Examples

Print to stdout without writing a file:

```bash
bash changelog.sh --repo . --stdout
```

Generate from a specific tag/range:

```bash
bash changelog.sh --repo . --since v1.2.0 --version v1.3.0
```

Run the test suite:

```bash
python3 -m unittest discover -v
```

## What makes it different

Most quick changelog scripts only dump raw commit subjects. This one adds release-review context:

- conventional commit parsing with scopes (`feat(api): ...` → `Added` / `api`)
- keyword fallback for non-conventional commits
- breaking-change extraction from `!` and `BREAKING CHANGE:` footers
- grouped Markdown output in a Keep-a-Changelog-like shape
- GitHub compare links when `origin` points at GitHub
- PR links from `(#123)` suffixes
- short SHA and author metadata for auditability
- no Python package install required

## Sample output

```md
# Changelog

All notable changes are generated from git history.

## [Unreleased] - 2026-05-14

[Compare changes](https://github.com/example/repo/compare/v1.2.0...HEAD)

### Breaking Changes

- **BREAKING**: drop old config format ([`fed9999`](https://github.com/example/repo/commit/fed9999), by Cara)
  - Migration note: config v1 removed

### Added

- **api**: add export endpoint ([#42](https://github.com/example/repo/pull/42), [`abc1234`](https://github.com/example/repo/commit/abc1234), by Alice)

### Fixed

- **cli**: handle empty repositories ([`def5678`](https://github.com/example/repo/commit/def5678), by Bob)
```
