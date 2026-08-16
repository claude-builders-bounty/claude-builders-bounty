# changelog-gen

Generate a structured `CHANGELOG.md` from your project's git history in one command.

## Setup (3 steps)

1. **Copy** `changelog_gen.py` into your project root.
2. **Install** Python 3.10+ and [git](https://git-scm.com) (both already present in most dev environments).
3. **Run** from anywhere inside the repo:

```bash
python changelog_gen.py
```

## What it does

- Fetches commits since the **last git tag** (`git describe --tags`); falls back to `--from-tag <tag>` or full history.
- Auto-categorizes every commit into **Added / Fixed / Changed / Removed** using smart keyword rules.
- Writes a clean, link-ready `CHANGELOG.md` with commit SHAs and authors.

## Options

| Flag | Description |
|---|---|
| `--out FILE` | Output file (default `CHANGELOG.md`) |
| `--from-tag TAG` | Generate entries since a specific tag |

## Example output

```markdown
# Changelog

All notable changes to this project, since tag `v1.2.0`.

## Added

- feat: add dark mode support ([`a1b2c3d`](...)) — Alice

## Fixed

- fix: handle empty input in parser ([`d4e5f6g`](...)) — Bob

## Changed

- refactor: simplify config loading ([`h7i8j9k`](...)) — Carol
```

> Tip: add `changelog_gen.py` to your CI (e.g. a `pre-release` job) so every release ships an up-to-date changelog.
