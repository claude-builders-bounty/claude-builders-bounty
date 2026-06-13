# Changelog Generator

Auto-generate a structured `CHANGELOG.md` from your git history.

## Setup

1. Copy `changelog-generator/` into your project
2. Make the script executable: `chmod +x changelog-generator/changelog.sh`
3. Run: `bash changelog-generator/changelog.sh`

## Usage

```bash
# Generate from the latest tag
bash changelog-generator/changelog.sh

# Custom range and output
bash changelog-generator/changelog.sh --since v1.0.0 --output docs/CHANGELOG.md

# From a different repo
bash changelog-generator/changelog.sh --repo ../my-project
```

## Claude Code Integration

Place `changelog-generator/SKILL.md` in your project and use:
```
/generate-changelog
```

## Output

Commits are auto-categorized into **Added**, **Fixed**, **Changed**, and **Removed** based on conventional commit keywords. See `samples/CHANGELOG.sample.md` for example output.
