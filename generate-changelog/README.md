# Generate Changelog

Create a structured `CHANGELOG.md` from git history with one dependency-free bash script.

## Setup

1. Copy `changelog.sh` and the `generate-changelog/` folder into any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## What It Does

- Reads commits since the latest git tag, or all commits when the repository has no tags.
- Categorizes changes into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown changelog with commit hashes and commit dates.
- Works as a standalone shell command or through the included Claude Code skill instructions.

## Usage

```bash
bash changelog.sh
```

You can also run the bundled script directly:

```bash
bash generate-changelog/changelog.sh
```

Optional output path:

```bash
bash changelog.sh --output RELEASE_NOTES.md
```

Use a specific range instead of the latest tag:

```bash
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
```

Preview without writing a file:

```bash
bash changelog.sh --dry-run
```

## Categorization Rules

| Category | Commit prefixes and keywords |
|---|---|
| Added | `feat`, `feature`, `add`, `create`, `implement`, `introduce` |
| Fixed | `fix`, `bug`, `bugfix`, `patch`, `resolve`, `repair` |
| Removed | `remove`, `delete`, `drop`, `deprecate`, `prune` |
| Changed | `change`, `update`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`, and uncategorized commits |

Conventional commit scopes are supported, for example `feat(api): add login endpoint`.

## Test Run

`SAMPLE_OUTPUT.md` was generated from this repository's real git history with:

```bash
bash generate-changelog/changelog.sh --dry-run > generate-changelog/SAMPLE_OUTPUT.md
```
