# CHANGELOG Generator Skill

Automatically generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `generate-changelog.sh` to your project:
   ```bash
   cp skills/generate-changelog/generate-changelog.sh /your/project/
   ```

2. Make it executable:
   ```bash
   chmod +x generate-changelog.sh
   ```

3. Run it:
   ```bash
   bash generate-changelog.sh
   ```

## Usage

```bash
# Generate CHANGELOG for current repo
bash generate-changelog.sh

# Generate CHANGELOG for a specific repo
bash generate-changelog.sh /path/to/repo
```

## Output format

Commits are auto-categorized into:
- **Added** — `feat:` commits
- **Fixed** — `fix:` commits
- **Changed** — `chore:`, `refactor:`, `style:` commits
- **Removed** — commits containing "remove", "deprecate", "delete"
