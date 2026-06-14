# CHANGELOG Generator

Generate a beautiful, structured `CHANGELOG.md` from your git history.

## Setup & Usage

1. **Run the script** in any git repository:
   ```bash
   python /path/to/changelog.py
   ```

2. **Review** the generated `CHANGELOG.md`

3. **Customize** (optional):
   ```bash
   python /path/to/changelog.py --output docs/HISTORY.md --repo /my/project
   ```

## How It Works

The script finds commits since the last git tag, parses conventional commit messages (feat:, fix:, chore:, etc.), and auto-categorizes them into Added / Fixed / Changed / Removed sections.

Merge commits and version bumps are automatically filtered out.

## Requirements

- Python 3.6+
- Git

## Sample Output

```markdown
# Changelog

> Generated on 2025-06-14

## Added
- **User authentication via OAuth2** (a1b2c3d) - Jane Doe
- **Dark mode toggle** (e4f5g6h) - John Smith

## Fixed
- **Crash on empty search results** (i7j8k9l) - Jane Doe

## Changed
- **Upgraded dependencies to latest versions** (m0n1o2p) - Dependabot
```
