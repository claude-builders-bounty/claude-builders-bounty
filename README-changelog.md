# CHANGELOG Generator

Auto-generate structured `CHANGELOG.md` from git history using conventional commits.

## Setup

1. Copy `generate-changelog.sh` into your project root
2. Run `chmod +x generate-changelog.sh`
3. Run `./generate-changelog.sh`

## Usage

```bash
# Generate changelog from latest tag
./generate-changelog.sh

# Generate from a specific tag
./generate-changelog.sh --since v1.0.0 --tag v2.0.0

# Custom output file
./generate-changelog.sh --output docs/CHANGELOG.md
```

## Output

Sections are auto-categorized: 🚀 Features, 🐛 Bug Fixes, ⚡ Performance, ♻️ Refactoring, 📝 Documentation, and more.