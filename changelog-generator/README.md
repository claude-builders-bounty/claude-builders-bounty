# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog-generator/generate_changelog.py` and `.claude/commands/generate-changelog.md` into your project.
2. Run `/generate-changelog` in Claude Code, or run the Python script directly.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

Claude Code slash command:

```text
/generate-changelog
```

Direct script usage:

```bash
python3 changelog-generator/generate_changelog.py --output CHANGELOG.md
```

Use a specific start ref:

```bash
python3 changelog-generator/generate_changelog.py --from v1.2.0 --version v1.3.0
```

## Categories

Commits are grouped into:

- `Added`: `feat`, `feature`, `add`, `new`
- `Fixed`: `fix`, `bug`, `bugfix`, `patch`
- `Changed`: `change`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`

Unknown commit prefixes go under `Changed` so the output is complete instead of silently dropping commits.
