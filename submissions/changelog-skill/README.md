# Changelog Generator

Generate a structured CHANGELOG.md from git history.

## Setup (2 steps)

1. Copy `SKILL.md` to your project's `.claude/skills/` directory
2. Use `/generate-changelog` in Claude Code

**Or** use the bash script directly:

```bash
curl -O https://raw.githubusercontent.com/TateLyman/claude-builders-bounty/feat/changelog-skill/submissions/changelog-skill/changelog.sh
chmod +x changelog.sh
./changelog.sh
```

## How It Works

- Finds the latest git tag as the version anchor
- Categorizes commits by prefix (feat:, fix:, refactor:, etc.)
- Outputs a properly formatted CHANGELOG.md

## Sample Output

See [sample-output.md](./sample-output.md) for a real-world example.
