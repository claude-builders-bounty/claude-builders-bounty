# Pre-commit Hook Agent

A pre-commit hook that validates Python code quality before every commit.

## What it checks

| Check | Tool | What it catches |
|---|---|---|
| Import order | isort | Unsorted or incorrectly grouped imports |
| Unused imports | ruff (F401) | Imported names that are never used |
| Type annotations | AST | Public functions missing return/parameter type hints |
| Docstrings | AST | Public functions missing docstrings |

## Setup (3 steps)

**1. Install dependencies**

```bash
pip install isort ruff pre-commit
```

**2. Install the pre-commit hook**

```bash
pre-commit install
```

**3. Commit with confidence**

The hook runs automatically on every `git commit` involving Python files. If issues are found, the commit is blocked and you'll see a clear report:

```
1/4 Checking import order (isort)... FAIL
 - mymodule.py: import order needs fixing (run `isort mymodule.py`)
2/4 Checking unused imports (ruff F401)... PASS
3/4 Checking type annotations on public functions... FAIL
 - mymodule.py:42: function 'process' missing return type annotation
4/4 Checking docstrings on public functions... PASS

Pre-commit check FAILED. Fix the issues above before committing.
```

## Manual run

```bash
# Check only staged files
python precommit_hook/precommit_hook.py

# Check all tracked Python files
PRE_COMMIT_ALL_FILES=1 python precommit_hook/precommit_hook.py
```

## CI integration

In GitHub Actions, the script automatically posts a comment on the PR listing any issues found. No extra configuration needed — just set `CI=true` (which GitHub Actions does by default).

## Skipping the hook

```bash
git commit --no-verify
```

Use sparingly — the hook exists to keep code clean.
