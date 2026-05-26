# Pre-commit Hook Agent

## Description

A Claude Code sub-agent that validates Python code quality as a pre-commit hook. It runs four checks on every commit containing Python files and blocks the commit if issues are found.

## Checks Performed

1. **Import Order** — Uses `isort --check-only` to verify imports are sorted correctly.
2. **Unused Imports** — Uses `ruff check --select F401` to detect unused imports.
3. **Type Annotations** — AST-based check that all public functions (non `_`-prefixed) have return type and parameter type annotations.
4. **Docstrings** — AST-based check that all public functions have docstrings.

## Usage

### As a pre-commit hook (automatic)

After setup (see README.md), the hook runs automatically on `git commit` for any staged Python files.

### As a Claude Code sub-agent

Invoke the agent directly:

```bash
python precommit_hook/precommit_hook.py
```

To check all Python files in the repo (not just staged):

```bash
PRE_COMMIT_ALL_FILES=1 python precommit_hook/precommit_hook.py
```

### In CI (GitHub Actions)

The script detects when running in GitHub Actions and automatically posts a comment on the PR summarizing any issues found.

## Environment Variables

| Variable | Description |
|---|---|
| `PRE_COMMIT_ALL_FILES` | Set to `1` to check all tracked Python files instead of only staged files |
| `CI` | Set automatically in GitHub Actions; enables PR comment posting |

## Exit Codes

- `0` — All checks passed
- `1` — One or more checks failed

## Dependencies

- Python 3.9+
- `isort` (for import order checking)
- `ruff` (for unused import checking)
- `gh` CLI (optional; for PR comment posting in CI)
