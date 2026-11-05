# Generate Changelog Skill

Generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Ensure git is installed: `git --version`
2. Run the script: `bash changelog.sh` (from project root)
3. Check the output: `cat CHANGELOG.md`

## Usage

```bash
# Direct:
bash changelog.sh [output_file] [repo_dir]

# As a Claude Code skill:
/generate-changelog
```

## Output

A `CHANGELOG.md` with:
- Version and date header
- Auto-categorized commits (Added / Fixed / Changed / Removed)
- Formatted in Keep a Changelog style
