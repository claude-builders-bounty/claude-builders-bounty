# Generate Changelog Skill

Structured `CHANGELOG.md` generator for Claude Code and bash.

## Setup (3 steps)

1. Copy `skills/generate-changelog/` into your repo (or use this monorepo path as-is).
2. Make the script executable: `chmod +x skills/generate-changelog/changelog.sh`
3. Run: `bash skills/generate-changelog/changelog.sh`

## Claude Code

Add this folder to your project's skills directory, then invoke:

```
/generate-changelog
```

Claude will run `changelog.sh` and commit or show the generated file.

## Sample output

See [`sample-output/CHANGELOG.sample.md`](sample-output/CHANGELOG.sample.md) — generated from this repository's git history.

## Options

```bash
# Default: write ./CHANGELOG.md
bash skills/generate-changelog/changelog.sh

# Custom output path
bash skills/generate-changelog/changelog.sh docs/CHANGELOG.md
```
