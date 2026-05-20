---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history. Categorises commits into Added / Fixed / Changed / Removed / Security / Deprecated using conventional-commit prefixes and keyword heuristics.
---

# generate-changelog

## Description

This skill runs `changelog.sh` inside the current project to produce a
well-structured `CHANGELOG.md` from git commit history (since the last tag,
or the full history).

## Modes

| Command               | Behaviour                                      |
|-----------------------|------------------------------------------------|
| `/generate-changelog` | Commits since last tag → `CHANGELOG.md`        |
| `--all`               | Full repo history                              |
| `--range=v1.0..v2.0`  | Custom revision range                          |
| `--output=FILE`       | Write to a custom file                         |

## Acceptance criteria

- [x] Works via `/generate-changelog` or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorises into Added / Fixed / Changed / Removed / Deprecated / Security
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (sample output included)
- [x] README with 3-step setup

## Categorisation rules

1. **Conventional commits** (highest priority): `feat:`→Added, `fix:`→Fixed,
   `chore:`/`refactor:`/`docs:`/`test:`/`ci:`/`build:`/`perf:`→Changed,
   `revert:`→Removed, `security:`→Security, `deprecate:`→Deprecated
2. **Keyword fallback**: scans commit message for words like "fix/bug/hotfix"
   → Fixed, "add/new/introduce/implement" → Added, etc.
3. **Default**: everything else → Changed

## Sample output

See [CHANGELOG.sample.md](./CHANGELOG.sample.md) — generated from this repo's own git history.
