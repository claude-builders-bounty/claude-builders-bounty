# Generate Changelog Skill

A small Claude Code-friendly changelog generator that turns git history into a structured `CHANGELOG.md`.

## Setup in 3 steps

1. Copy `changelog.sh` into the root of any git repository.
2. Run `chmod +x changelog.sh`.
3. Run `./changelog.sh` or `./changelog.sh CUSTOM_CHANGELOG.md`.

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads non-merge commits from `latest-tag..HEAD`; if no tags exist, it uses the full history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a properly formatted Markdown changelog.

## Claude Code usage

Ask Claude Code:

```text
Run ./changelog.sh to generate a changelog for this repository.
```

The script is intentionally plain Bash so it can be used directly from Claude Code without extra dependencies.
