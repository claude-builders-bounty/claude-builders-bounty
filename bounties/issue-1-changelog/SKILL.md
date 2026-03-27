# Skill: generate-changelog

Generate a structured `CHANGELOG.md` from git history.

## Trigger

User says: `/generate-changelog`

## Instructions

1. Run the changelog generator:
   ```bash
   python3 bounties/issue-1-changelog/changelog.py
   ```

2. If the user specifies a range, use `--since`:
   ```bash
   python3 bounties/issue-1-changelog/changelog.py --since v1.0.0
   ```

3. To preview without writing:
   ```bash
   python3 bounties/issue-1-changelog/changelog.py --dry-run
   ```

4. Read the generated `CHANGELOG.md` and present it to the user.

## Options

| Flag | Description |
|------|-------------|
| `--since TAG` | Start from a specific tag or commit (default: latest tag) |
| `--output FILE` | Output file path (default: `CHANGELOG.md`) |
| `--version VER` | Override version in header (default: auto-detect from package.json/pyproject.toml/Cargo.toml) |
| `--dry-run` | Print to stdout instead of writing file |

## Categories

Commits are auto-classified by conventional commit prefix or natural language keywords:

- **Added** — feat, add, new, implement, create
- **Fixed** — fix, bug, patch, hotfix, resolve
- **Changed** — refactor, perf, improve, update, chore, docs, test
- **Removed** — remove, delete, drop, deprecate, revert
- **Security** — security, vuln, CVE, XSS, injection
