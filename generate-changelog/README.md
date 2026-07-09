# generate-changelog

Generate a structured, [Keep a Changelog](https://keepachangelog.com/)-style
`CHANGELOG.md` from a repository's **git history** — commits since the last tag,
auto-categorized into **Added / Fixed / Changed / Removed**.

Works two ways: a portable `bash changelog.sh` script, or the native Claude Code
skill `/generate-changelog`.

## Setup (3 steps)
1. Copy `changelog.sh` to your repository root (for Claude Code, also copy
   `.claude/skills/generate-changelog/SKILL.md`).
2. Make it executable: `chmod +x changelog.sh`
3. Run it from the repo: `bash changelog.sh` — writes `CHANGELOG.md` at the root.

That's it. In Claude Code you can instead just say `/generate-changelog`.

## Usage
```bash
bash changelog.sh [REPO_DIR] [OUTPUT_FILE]
#   REPO_DIR     git repo to read   (default: current directory)
#   OUTPUT_FILE  changelog to write (default: <REPO_DIR>/CHANGELOG.md)
```

## How commits are categorized
| Category | Matched commit prefixes / keywords |
|----------|-------------------------------------|
| Added    | `feat`, `feature`, `add`, "new …", "introduce …" |
| Fixed    | `fix`, `bugfix`, `hotfix`, "resolve …" |
| Removed  | `remove`, `delete`, `revert`, `deprecate`, `drop` |
| Changed  | everything else (`refactor`, `perf`, `docs`, `chore`, `style`, `update`, …) |

Conventional-Commit scopes (`feat(core): …`) are recognized. Merge commits are skipped.

See [`CHANGELOG.sample.md`](./CHANGELOG.sample.md) for real sample output.

## Requirements
`git` and `bash` (standard on Linux/macOS and Git for Windows). No network, no
other dependencies.
