# Generate Changelog Skill

Use this skill when the user asks Claude Code to generate or refresh a `CHANGELOG.md` from git history.

## Command

```bash
bash changelog.sh --repo . --output CHANGELOG.md --version Unreleased
```

## What it does

- Detects the latest git tag and reads commits from `<latest-tag>..HEAD`.
- Falls back to all history when a repository has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Pulls out breaking changes from `!` conventional commits and `BREAKING CHANGE:` footers.
- Preserves useful review metadata: scope, PR number, short SHA, author, compare link.
- Writes a Keep-a-Changelog-style Markdown file.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
bash changelog.sh --repo . --version v1.4.0 --since v1.3.0
bash changelog.sh --repo . --stdout
```

## Review checklist

Before submitting a PR, run:

```bash
python3 -m unittest discover -v
bash changelog.sh --repo . --stdout
```

Then include a small sample output in the PR body.
