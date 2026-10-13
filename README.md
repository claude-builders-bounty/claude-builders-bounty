# generate-changelog

Generate a structured `CHANGELOG.md` from a project's git history.
Commits since the last tag are auto-categorized into **Added / Fixed / Changed / Removed**
and written in [Keep a Changelog](https://keepachangelog.com/) format.

## Setup (3 steps)

1. Copy `changelog.sh` into the repository you want a changelog for.
2. Run it:
   ```bash
   bash changelog.sh --version v1.0.0
   ```
3. Commit the generated `CHANGELOG.md`.

Requires `git` and `bash`. No dependencies, no network, no API keys.

## Usage

```bash
bash changelog.sh                     # since the last tag, section "Unreleased"
bash changelog.sh --version v1.3.0    # name the section explicitly
bash changelog.sh --since v1.2.0      # explicit range start
bash changelog.sh --out docs/CHANGELOG.md
bash changelog.sh --repo /path/to/repo
bash changelog.sh --dry-run           # print to stdout, write nothing
bash changelog.sh --help
```

| Option | Meaning | Default |
|---|---|---|
| `--version` | section label | `Unreleased` |
| `--since` | range start (tag or commit) | newest tag, else all history |
| `--out` | output file | `CHANGELOG.md` |
| `--repo` | repository path | `.` |
| `--dry-run` | preview only | off |

## How commits are categorized

| Commit | Section |
|---|---|
| `feat: ...`, `feat(api): ...`, `add: ...` | Added |
| `fix: ...`, `fix(ui): ...`, `hotfix: ...` | Fixed |
| `remove: ...`, `revert: ...`, `deprecate: ...` | Removed |
| `refactor|perf|docs|chore|style|test|build|ci|update|rename|move: ...` | Changed |
| free-form subject containing `fix`/`bug` | Fixed |
| free-form subject containing `add`/`new` | Added |
| free-form subject containing `remove`/`delete`/`drop` | Removed |
| anything else | Changed (nothing is dropped) |

Scope and breaking-change markers are supported: `feat(api)!: drop v1` → Added.
Merge commits are skipped.

## Also usable as a Claude Code skill

`SKILL.md` is included, so the same tool is available as the `/generate-changelog`
skill — ask for a changelog and it runs the script above.

## Sample output

`SAMPLE-OUTPUT.md` contains real output produced on two public repositories:

- `claude-builders-bounty/claude-builders-bounty` (no tags → whole history),
- `sindresorhus/p-limit` (84 commits, 27 tags → range `v7.0.0..HEAD`).

## Tests

```bash
bash tests/test_changelog.sh
```

Ten assertions cover: each category (including conventional scopes), exclusion of
commits before the last tag, `--since` override, whole-history mode when no tags
exist, file writing, non-git directory failing with exit 2, and merge commits
being skipped.

## License

MIT — use it anywhere.
