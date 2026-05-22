# generate-changelog

Generate a Keep-a-Changelog style `CHANGELOG.md` from git history since the last tag. Auto-categorizes commits into **Added / Fixed / Changed / Removed** using Conventional Commits prefixes and keyword heuristics.

## Setup (3 steps)

1. Copy `changelog.sh` to your repo root, and `SKILL.md` to `.claude/skills/generate-changelog/SKILL.md` (or anywhere Claude Code picks up skills).
2. Make the script executable: `chmod +x changelog.sh`
3. Run it:
   - From shell: `bash changelog.sh > CHANGELOG.md`
   - From Claude Code: `/generate-changelog`

## Usage examples

```bash
# Default: from last tag to HEAD, auto-bump patch version
bash changelog.sh > CHANGELOG.md

# Specify a starting tag explicitly
bash changelog.sh --since v1.0.0 > CHANGELOG.md

# Specify the new version label
bash changelog.sh --next-version v2.0.0 > CHANGELOG.md
```

## How it works

1. Finds the last git tag (`git describe --tags --abbrev=0`)
2. Lists non-merge commits since that tag (`git log <tag>..HEAD --no-merges`)
3. Classifies each by Conventional Commits prefix or keyword heuristics
4. Emits a Keep-a-Changelog formatted Markdown block

See [example_output/CHANGELOG.md](example_output/CHANGELOG.md) for a real sample generated against the upstream `isaacs/node-tar` repository.

## License

MIT
