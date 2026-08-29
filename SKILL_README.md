# Generate Changelog Skill

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `SKILL.md` to your project's `.claude/skills/` directory (or use as standalone script)
2. Ensure your repo uses [Conventional Commits](https://www.conventionalcommits.org/) format
3. Run: `bash changelog.sh` or invoke `/generate-changelog` in Claude Code

## Usage

```bash
# Generate CHANGELOG.md in current directory
bash changelog.sh

# Specify output file
bash changelog.sh docs/CHANGELOG.md
```

## Categories

| Commit Prefix | Category |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `style:`, `perf:` | Changed |
| `revert:`, `remove:`, `delete:` | Removed |
| Other | Changed |

## Sample Output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for a live example generated from this repo's own history.
