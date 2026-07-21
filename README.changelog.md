# Changelog Generator

Generates a structured `CHANGELOG.md` from git history using conventional commit prefixes.

## Setup

1. **Download** — place `changelog.sh` in your project root
2. **Run** — `bash changelog.sh`
3. **Review** — open `CHANGELOG.md`

### Options

| Flag | Description |
|------|-------------|
| `--tag v1.0.0` | Generate changelog from a specific tag |
| `--from abc123` | Generate changelog from a specific commit ref |

### Commit Categorization

| Prefix | Section |
|--------|---------|
| `feat:` / `feature:` | Added |
| `fix:` / `bugfix:` | Fixed |
| `refactor:` | Changed |
| `remove:` / `deprecate:` / `delete:` | Removed |
| `chore:` / `docs:` / `test:` | _(excluded)_ |
| _unknown_ | Changed |
