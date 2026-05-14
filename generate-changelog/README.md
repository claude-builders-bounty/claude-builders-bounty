# Generate Changelog

`changelog.sh` builds a structured `CHANGELOG.md` from git commits since the latest tag. It works in any git repository and has no dependencies beyond Bash and Git. This package also includes a native Claude Code `SKILL.md` and `/generate-changelog` command wrapper.

## Setup

1. Copy `changelog.sh` into your repository root.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## What It Does

- Fetches tags from `origin` when available so the latest release tag is visible locally.
- Uses `git describe --tags --abbrev=0` to find the latest reachable tag.
- Reads commits from `<latest-tag>..HEAD`, or all history when no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Prepends a dated `Unreleased` section to `CHANGELOG.md` without deleting older entries.

## Categorization Rules

| Section | Commit subjects that match |
| --- | --- |
| Added | `feat:`, `add`, `create`, `new`, `introduce`, `implement` |
| Fixed | `fix:`, `hotfix:`, `bug`, `resolve`, `patch` |
| Removed | `remove`, `delete`, `drop`, `deprecate` |
| Changed | Everything else, including `docs:`, `refactor:`, `test:`, `chore:` |

Conventional commit prefixes such as `feat(api):` are stripped from the changelog entry while the short commit hash is kept for traceability.

## Options

```bash
CHANGELOG_OUTPUT=docs/CHANGELOG.md bash changelog.sh
CHANGELOG_FETCH_TAGS=0 bash changelog.sh
```

`CHANGELOG_OUTPUT` changes the destination file. `CHANGELOG_FETCH_TAGS=0` skips the best-effort `git fetch --tags origin` step for offline environments.

## Test

```bash
bash tests/test-changelog.sh
```

## Tested Repository

The included sample output was generated against the real GitHub repository `claude-builders-bounty/claude-builders-bounty` using the same script. See `examples/sample-output-claude-builders-bounty.md`.

The tag-range behavior was also checked against a local fixture with a `v1.0.0` tag and three later commits. The generated output used only `v1.0.0..HEAD` and placed the commits into `Added`, `Fixed`, and `Removed`.
