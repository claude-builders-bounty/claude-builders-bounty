# Generate Changelog Skill

A Claude Code skill + bash script that auto-generates a structured
`CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `skills/generate-changelog/` to your project
2. Run `chmod +x skills/generate-changelog/changelog.sh`
3. Run `bash skills/generate-changelog/changelog.sh`

That's it. Or use `/generate-changelog` in Claude Code.

## Usage

```bash
# Generate CHANGELOG.md for commits since last tag
bash changelog.sh

# Preview without writing to file
bash changelog.sh --dry-run

# Specify a starting tag
bash changelog.sh --since v1.0.0
```

## Features

- Auto-categorizes commits into **Added / Fixed / Changed / Removed**
- Detects conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to keyword heuristics for non-conventional commits
- Auto-detects version from latest git tag
- Prepends to existing CHANGELOG.md if one exists
- Pure bash — zero dependencies beyond `git`

## Sample Output

See `sample-output.md` for an example generated from a real open-source project
(Hermes Agent, 10,000+ commits).
