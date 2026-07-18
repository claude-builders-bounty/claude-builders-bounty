---
name: changelog-generator
description: Generate a Keep-a-Changelog formatted CHANGELOG.md from git history.
trigger: /generate-changelog
version: 1.0.0
inputs:
  - name: since_tag
    type: string
    required: false
    description: "Only include commits after this git tag (e.g. v1.0.0)."
  - name: since
    type: string
    required: false
    description: "Only include commits after this ISO date (e.g. 2026-01-01)."
  - name: limit
    type: integer
    required: false
    default: 200
    description: "Max number of commits to include."
  - name: out
    type: string
    required: false
    default: CHANGELOG.md
    description: "Output file path."
outputs:
  - CHANGELOG.md (Markdown)
---

# changelog-generator

Auto-generates a Keep-a-Changelog `CHANGELOG.md` from your git history.

## What it does

1. Reads commits since the last tag (or all reachable history by default)
2. Auto-buckets each commit into one of **Added / Changed / Fixed / Removed / Deprecated / Security**
3. Writes a clean `CHANGELOG.md` ready for humans and tooling

## Conventional Commits support

If your commits use the Conventional Commits format (`feat:`, `fix:`, `refactor:`, …),
the type maps directly to a category:

| Prefix | Category |
|---|---|
| `feat`, `feature`, `add` | Added |
| `fix`, `bugfix` | Fixed |
| `refactor`, `perf`, `chore`, `docs`, `style`, `test`, `ci`, `build` | Changed |
| `remove`, `rm`, `delete` | Removed |
| `deprecate` | Deprecated |
| `security`, `sec` | Security |

If the message doesn't use a recognised prefix, the script falls back to
keyword matching (`add`, `bug`, `refactor`, `docs`, `security`, …).

## Usage

### From Claude Code slash command

```
/generate-changelog
/generate-changelog since_tag=v1.0.0
/generate-changelog since=2026-01-01 limit=50
```

### From bash / CI

```bash
python3 skills/changelog-generator/changelog.py
python3 skills/changelog-generator/changelog.py --since-tag v1.0.0 --out CHANGELOG.md
```

## Options

| Flag | Default | Notes |
|------|---------|-------|
| `--since-tag` | none | Pass `v0.9.0` to limit range |
| `--since` | none | ISO date string |
| `--limit` | 200 | Cap on number of commits read |
| `--out` | `CHANGELOG.md` | Where to write |
| `--top-per-section` | 0 (off) | Cap each section to N items |
| `--repo-name` | none | Override repo label in header |

## Acceptance criteria

- ✅ Works via `/generate-changelog` slash command or `python3 changelog.py`
- ✅ Fetches commits since the last git tag (with `--since-tag`)
- ✅ Auto-categorises into Added / Fixed / Changed / Removed (more on demand)
- ✅ Outputs a properly formatted `CHANGELOG.md`
- ✅ Tested on a real GitHub repo (sample output in `SAMPLE_CHANGELOG.md`)
- ✅ README with setup instructions in 3 steps or fewer
