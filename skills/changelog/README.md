# CHANGELOG Generator Skill

Generate a structured `CHANGELOG.md` from `git log` since the last tag.

## Install

Copy `changelog.sh` to your repo root and `chmod +x changelog.sh`.

## Usage

```bash
./changelog.sh            # since last tag
./changelog.sh v1.2.0     # since v1.2.0
```

Output categories: Added / Fixed / Changed / Removed (based on commit prefix).

## Why

$0 infra, no API — uses local git log only. Fits any repo.

## Test

Run `./changelog.sh` on any repo with tags — produces CHANGELOG.md sections.
