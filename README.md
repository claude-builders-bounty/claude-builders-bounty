# generate-changelog

> Generate a structured `CHANGELOG.md` from your project's git history. Auto-categorizes into Added / Fixed / Changed / Removed.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

## Use

```bash
./changelog.sh [output_file]
```

Examples:
```bash
./changelog.sh                    # writes CHANGELOG.md
./changelog.sh HISTORY.md         # writes HISTORY.md
./changelog.sh CHANGELOG.md >>   # appends to existing file (manual)
```

## How it works

1. Finds the latest git tag
2. Collects all commits since that tag
3. Categorizes each commit by conventional-commit prefix or keyword heuristics
4. Writes a properly formatted `CHANGELOG.md`

## Categorization rules

| Commit prefix / keyword | Category |
|------------------------|----------|
| `feat`, `add`, `new`, `implement`, `support` | **Added** |
| `fix`, `bugfix`, `hotfix`, `resolve`, `repair` | **Fixed** |
| `remove`, `delete`, `drop`, `deprecate`, `clean` | **Removed** |
| `refactor`, `perf`, `chore`, `deps`, `style`, `ci`, `docs`, `security`, `update`, `upgrade`, `improve`, `optimize` | **Changed** |
| `BREAKING CHANGE` or `!:` suffix | **Changed** (breaking) |

## Requirements

- Bash 4+ (macOS: `brew install bash`)
- Git repository with at least one commit

## Example output

See [`CHANGELOG.md`](CHANGELOG.md) in this repo for a live sample.

---

*Assisted-by: Claude (Anthropic)*
