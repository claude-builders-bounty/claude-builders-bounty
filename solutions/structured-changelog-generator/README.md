# Structured CHANGELOG Generator

A dependency-free Bash CLI and Claude Code skill that turns Git history since the latest tag into a [Keep a Changelog](https://keepachangelog.com/) document.

## Setup (2 steps)

1. Copy `changelog.sh` into a Git repository and make it executable: `chmod +x changelog.sh`.
2. Run `bash changelog.sh`.

The result is written to `CHANGELOG.md`. No API token, network call, or package installation is required.

## Usage

```bash
bash changelog.sh
bash changelog.sh --from v1.2.0 --to HEAD
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --stdout
```

For Claude Code, copy `SKILL.md` into the relevant skill directory and invoke `/generate-changelog`.

## Categorization

- **Added:** `feat:`, `feature:`, `add:`, `new:`
- **Fixed:** `fix:`, `bugfix:`, `hotfix:`
- **Removed:** `remove:`, `delete:`, `deprecate:`
- **Changed:** all other commits, including refactors, documentation, build, and performance changes
- Breaking conventional commits such as `feat!:` and bodies containing `BREAKING CHANGE` are clearly marked under **Changed**.

Merge commits are excluded. Each entry includes its short commit hash for traceability. If no tag exists, the full reachable history is used.

## Safety

The script only reads Git history and writes the selected output file. `--stdout` performs no file write. It never creates tags, commits, pushes, or changes repository configuration.

## Test

Run `bash tests/test_changelog.sh`. The test creates an isolated real Git repository with a tag and representative commits, runs the CLI, and verifies every required category and the tag boundary.

A checked-in demonstration is available at `examples/SAMPLE_CHANGELOG.md`.
