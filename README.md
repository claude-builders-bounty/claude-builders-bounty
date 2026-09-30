# Changelog Generator

A bash script that auto-generates a structured `CHANGELOG.md` from git history by categorizing conventional commits.

## Quick Start

1. **Download**: `curl -O https://raw.githubusercontent.com/astra-intelligence/claude-builders-bounty/main/changelog.sh && chmod +x changelog.sh`
2. **Run**: `bash changelog.sh --repo /path/to/your/project`
3. **Done**: Open `CHANGELOG.md` in your project root

## How It Works

The script reads commits from the last git tag to HEAD, parses conventional commit prefixes (`feat:`, `fix:`, `chore:`, etc.), and categorizes each line into:

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `chore:` / `refactor:` / `perf:` / `docs:` | Changed |
| `revert:` / `remove:` | Removed |
| `deprecat:` | Deprecated |
| `security:` | Security |

Uncategorized commits fall into **Changed**.

## Options

```
Usage: bash changelog.sh [--since TAG] [--repo PATH] [--output FILE]

  --since TAG   Start from this tag (default: latest tag, or all commits)
  --repo PATH   Path to git repository (default: current directory)
  --output FILE Output file path (default: CHANGELOG.md)
```

## Example

```bash
# Generate changelog from last release to HEAD
bash changelog.sh --repo ~/projects/my-app

# From a specific tag
bash changelog.sh --since v1.0.0 --repo ~/projects/my-app

# Save to custom path
bash changelog.sh --repo ~/projects/my-app --output docs/releases.md
```

## Requirements

- Git (any version)
- Bash 4+