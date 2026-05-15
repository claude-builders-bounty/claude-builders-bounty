# Git Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your project's git history.

Commits are auto-categorized into **Added / Changed / Fixed / Removed / Deprecated / Security / Other** based on conventional-commit prefixes.

## Setup (3 steps)

### 1. Copy the script into your repo

```bash
cp changelog.sh /path/to/your/repo/
```

### 2. Tag your releases

```bash
git tag v1.0.0
git push --tags
```

### 3. Run it

```bash
cd /path/to/your/repo
bash changelog.sh
```

That's it — `CHANGELOG.md` is generated in your repo root.

## Usage

```bash
bash changelog.sh                    # from last tag to HEAD
bash changelog.sh v1.2.0             # from v1.2.0 to HEAD
bash changelog.sh v1.0.0 v2.0.0      # between two tags
```

Or use the Claude Code skill:

```
/generate-changelog
/generate-changelog v1.2.0
/generate-changelog v1.0.0 v2.0.0
```

## How it works

1. Finds the latest git tag (or uses the range you specify)
2. Collects all commits in that range
3. Classifies each commit by its prefix (`feat`, `fix`, `remove`, etc.)
4. Writes a Keep-a-Changelog formatted `CHANGELOG.md`
5. If a changelog already exists, **prepends** the new entry

## Commit conventions recognized

| Category   | Prefixes                                          |
|-----------|---------------------------------------------------|
| Added     | `feat`, `add`, `implement`, `create`, `support`   |
| Fixed     | `fix`, `bugfix`, `patch`, `resolve`, `hotfix`     |
| Changed   | `change`, `update`, `refactor`, `improve`, `bump` |
| Removed   | `remove`, `delete`, `drop`, `eliminate`           |
| Deprecated | `deprecate`, `deprecated`                        |
| Security  | `security`, `cve`, `vulnerability`                |

## Requirements

- Bash 4+
- Git
- No external dependencies
