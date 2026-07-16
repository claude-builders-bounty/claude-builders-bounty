# CHANGELOG Generator

Auto-generate structured `CHANGELOG.md` from git commit history.

## Setup (3 steps)

1. Clone the repository
2. Make the script executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Usage

```bash
# From last tag
bash changelog.sh

# Specific range
bash changelog.sh v1.0.0..v2.0.0

# Custom output
bash changelog.sh -o releases/v2.md
```

## Categories

Commits are categorized by conventional commit prefixes:
- **Added**: `feat:`, `feature:`, `new:`
- **Fixed**: `fix:`, `bugfix:`, `patch:`
- **Changed**: `refactor:`, `change:`, `modify:`
- **Removed**: `remove:`, `delete:`, `drop:`
- **Security**: `security:`, `CVE-`, `vulnerability:`
