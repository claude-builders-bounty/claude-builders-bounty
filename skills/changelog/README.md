# Changelog Skill 📋

Generate structured CHANGELOG.md from git history.

## Install (3 steps)

```bash
# 1. Copy files
cp -r skills/changelog ~/.claude/skills/

# 2. Make executable
chmod +x ~/.claude/skills/changelog/changelog.sh

# 3. Use it
bash ~/.claude/skills/changelog/changelog.sh
```

## Usage

```bash
# Basic (auto-detect latest tag)
bash changelog.sh

# Custom output
bash changelog.sh docs/CHANGELOG.md

# With tag prefix
bash changelog.sh CHANGELOG.md v
```

## How It Works

1. Finds the latest git tag (or uses all commits if no tags)
2. Collects commits since that tag
3. Categorizes each commit by keyword prefix:
   - **Added**: `feat:`, `add:`, `new:`, `implement:`
   - **Fixed**: `fix:`, `bug:`, `resolve:`, `patch:`
   - **Changed**: `update:`, `refactor:`, `improve:`, `docs:`
   - **Removed**: `remove:`, `delete:`, `deprecate:`
   - **Other**: `chore:`, `ci:`, `build:`, `test:`
4. Outputs a formatted CHANGELOG.md

## Requirements

- Bash 4+
- Git

## License

MIT
