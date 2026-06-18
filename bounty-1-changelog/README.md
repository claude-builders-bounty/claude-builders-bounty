# generate-changelog

Bash script that builds a structured `CHANGELOG.md` from a project's git history.
Commits are auto-categorized into **Added / Fixed / Changed / Removed** based on their subject line prefix.

## Setup (3 steps)

**1. Download**
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/bounty-1-changelog/changelog.sh
chmod +x changelog.sh
```

**2. Run from your project root**
```bash
bash changelog.sh
```

**3. Done** — `CHANGELOG.md` is written to the current directory.

## Options

```bash
bash changelog.sh                        # commits since last tag → CHANGELOG.md
bash changelog.sh --since v1.2.0         # commits since a specific tag
bash changelog.sh --output HISTORY.md   # write to a custom file
```

## Categorization rules

| Prefix | Section |
|---|---|
| `feat`, `add`, `new`, `implement`, `create` | **Added** |
| `fix`, `bug`, `patch`, `resolve`, `correct` | **Fixed** |
| `refactor`, `update`, `change`, `improve`, `perf`, `style`, `chore`, `ci`, `docs` | **Changed** |
| `remove`, `delete`, `drop`, `deprecat` | **Removed** |
| anything else | **Other** |

Matching is case-insensitive and prefix-only — e.g. `feat(auth): ...` → Added.

## Sample output

See [`SAMPLE_CHANGELOG.md`](SAMPLE_CHANGELOG.md) — generated on the `claude-builders-bounty` repo.

## Requirements

- bash 4+
- git (any version with `git log` and `git describe`)
- No other dependencies
