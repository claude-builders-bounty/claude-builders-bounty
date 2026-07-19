# Generate Changelog Skill

Generates a structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x skills/generate-changelog/changelog.sh
```

## Usage

```bash
./skills/generate-changelog/changelog.sh
```

## Sample Output

```markdown
# Changelog

## 2026-07-19

### ✨ Added
- User authentication
- Dashboard layout

### 🐛 Fixed
- Login redirect issue
```

## Requirements

- Git repository with conventional commit prefixes (`Added:`, `Fixed:`, `Changed:`, `Removed:`)
- Bash 4+
