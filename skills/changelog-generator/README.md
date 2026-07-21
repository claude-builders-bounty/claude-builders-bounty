# CHANGELOG Generator

Auto-generates `CHANGELOG.md` from git history, categorized by type.

## Setup

```bash
# 1. Copy to your project
cp changelog.sh /path/to/your/project/

# 2. Make executable
chmod +x changelog.sh

# 3. Run
./changelog.sh
```

## Output

Categories: `Added`, `Fixed`, `Changed`, `Removed` — auto-detected from commit messages.

Conventional commit prefixes (`feat:`, `fix:`, etc.) are supported. Non-prefixed commits go to `Changed`.
