# CHANGELOG Generator Solution

A zero-dependency bash + Claude Code skill submission for bounty #1.

## 3-step setup

1. Copy `changelog.sh` and `SKILL.md` into the root of any git repository.
2. Run `chmod +x changelog.sh`.
3. Run `bash changelog.sh` to create or update `CHANGELOG.md`.

## Files included

- `changelog.sh` — git-history changelog generator
- `SKILL.md` — Claude Code `/generate-changelog` skill instructions
- `test_changelog.sh` — shell regression test using a temporary git repo
- `sample-output.md` — output generated from a real GitHub repository

## Features

- Finds the latest git tag automatically with `git describe --tags --abbrev=0`
- Falls back to full repository history when no tag exists
- Supports `--since-tag`, `--output`, and `--dry-run`
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`
- Highlights breaking changes from `!:` or `BREAKING CHANGE`
- Creates GitHub commit links when `origin` points to GitHub
- Preserves older release sections when updating an existing changelog
- Requires only bash and git

## Verification

Run:

```bash
bash -n changelog.sh
bash test_changelog.sh
```

The included `sample-output.md` was generated from the real GitHub repository `sindresorhus/ky` using:

```bash
bash changelog.sh --since-tag v2.0.2 --dry-run > sample-output.md
```
