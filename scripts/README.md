# scripts/changelog.sh

Generate a structured `CHANGELOG.md` from a project's git history.

## Setup

No dependencies — requires only `bash` and `git`.

## Usage

```bash
# In your project root:
bash scripts/changelog.sh

# Or specify a different repo:
bash scripts/changelog.sh --repo ../my-project

# Or since a specific tag:
bash scripts/changelog.sh --since v1.0.0
```

The script:

1. Finds the last git tag (or scans all history if none exists)
2. Categorizes commits into **Added** / **Fixed** / **Changed** / **Removed**
3. Outputs a well-formatted `CHANGELOG.md`

Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `remove:`) are recognized
automatically. Commits without a recognized prefix go into "Other".

## As a Claude Code Command

Add to your `CLAUDE.md`:

```
## Commands
- `bash scripts/changelog.sh` — Generate CHANGELOG.md from git history
```
