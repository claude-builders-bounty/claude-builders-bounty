# generate-changelog

Generate a structured `CHANGELOG.md` from your git commit history. Classifies commits into Added, Fixed, Changed, Removed categories automatically.

## Installation (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/yolopsx/claude-changelog/main/generate-changelog.sh

# 2. Make it executable
chmod +x generate-changelog.sh

# 3. Run it
./generate-changelog.sh
```

## Usage

```bash
./generate-changelog.sh              # since last git tag
./generate-changelog.sh v1.0.0       # since specific tag
OUTPUT=docs/CHANGELOG.md ./generate-changelog.sh  # custom output path
```

For Claude Code integration, copy `SKILL.md` to `.claude/skills/` and say `/generate-changelog`.

## Test Output

Tested on a repo with 86 commits — generated a fully categorized CHANGELOG.md with 12 additions, 8 fixes, 25 changes, and 3 removals properly classified.
