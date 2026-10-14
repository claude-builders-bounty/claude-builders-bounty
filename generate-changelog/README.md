# generate-changelog

Generate a structured `CHANGELOG.md` from git history — commits since the last tag, auto-categorized into **Added / Fixed / Changed / Removed** in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Works as a Claude Code skill (`/generate-changelog`) or a standalone bash script. Bash + git only, no other dependencies.

## Setup (3 steps)

1. Copy this `changelog-skill` folder anywhere on your machine.
2. *(Optional, for the Claude Code skill)* Copy the folder into `~/.claude/skills/generate-changelog/` so `/generate-changelog` is available.
3. Run it from any git repo: `bash changelog.sh`

## Usage

```bash
bash changelog.sh                                    # since last tag → ./CHANGELOG.md
bash changelog.sh --from v1.1.0 --to v1.2.0 --version 1.2.0
bash changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
```

| Option | Default | Meaning |
|---|---|---|
| `--repo <path>` | `.` | Git repo to read |
| `--from <ref>` | last tag | Start of range |
| `--to <ref>` | `HEAD` | End of range |
| `--version <v>` | `Unreleased` | Version header |
| `--date <YYYY-MM-DD>` | today | Release date |
| `--output <file>` | `<repo>/CHANGELOG.md` | Where to write |

The script prints the range it used to stderr (e.g. `since last tag v0.1.0`, or the no-tag fallback below) plus per-category counts.

## How commits are categorized

Conventional-commit prefixes are parsed (`type(scope)!: subject` or `type: subject`), stripped from the output, and mapped:

| Commit | Category |
|---|---|
| `feat:` | Added |
| `fix:` (also `bugfix`, `hotfix`) | Fixed |
| `remove:` / `revert:` types, or subjects starting with remove/delete/drop/deprecate | Removed |
| `refactor`, `perf`, `style`, `chore`, `docs`, `test`, `build`, `ci`, `types` | Changed |

Non-conventional subjects are matched by keywords (`add/introduce/implement` → Added, `fix/bugfix/patch/resolve` → Fixed, `remove/delete/drop/deprecate` → Removed). Anything unmatched lands in **Changed** — every commit in the range appears in the output; nothing is dropped silently. PR/issue refs like `(#123)` are preserved.

## Edge cases

- **No tags:** falls back to all commits from the root commit and prints `no tags found; using all commits from root <sha>`.
- **Empty range:** writes the version header with a `No changes in this range` note and exits 0.
- **Merge commits:** subjects starting with `Merge ` are skipped (their content arrives via the merged branch's own commits).

## Files

- `changelog.sh` — the generator (bash + git only)
- `SKILL.md` — Claude Code skill wrapper (`/generate-changelog`)
- `sample-output.md` — real output from [chalk](https://github.com/chalk/chalk), range `v5.6.2..v6.0.1`
- `tests/results.txt` — edge-case test log with observed outputs
