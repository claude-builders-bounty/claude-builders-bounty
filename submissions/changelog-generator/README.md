# Changelog Generator — Bounty Submission

Generates a structured `CHANGELOG.md` from git commits since the last tag.

## Setup (3 steps)

1. Copy `changelog.sh` anywhere on your PATH (or run from this folder).
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh /path/to/repo` — writes `CHANGELOG.md` in that repo.

## Claude Code

Add this folder to your skills path, then run `/generate-changelog`.

## Categories

| Prefix / keyword | Section |
|------------------|---------|
| fix, bug, patch | Fixed |
| remove, delete, drop | Removed |
| change, update, refactor, chore, docs | Changed |
| everything else | Added |

## Sample output

See [samples/CHANGELOG.sample.md](samples/CHANGELOG.sample.md).

## Test

```bash
bash changelog.sh ../../..
cat CHANGELOG.md
```
