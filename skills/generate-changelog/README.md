# generate-changelog

Generate a structured `CHANGELOG.md` from git history. Works as a Claude Code
skill (`/generate-changelog`) or a plain bash script (`changelog.sh`).

- Parses [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `feat(api)!: ...`).
- Groups commits into [Keep a Changelog](https://keepachangelog.com/) sections: **Added / Changed / Fixed / Removed**.
- Surfaces breaking changes (`!:` or `BREAKING CHANGE:`) at the top of the section.
- Defaults to commits **since the last git tag**; supports `--from`, `--to`, `--all`.
- Links each entry to the commit on GitHub when `origin` is set.

## Setup (3 steps)

1. **Copy the skill into your repo or `~/.claude/skills/`:**
   ```bash
   cp -R skills/generate-changelog ~/.claude/skills/
   ```
2. **Make the script executable** (optional, you can also call it via `bash`):
   ```bash
   chmod +x ~/.claude/skills/generate-changelog/changelog.sh
   ```
3. **Use it.** In Claude Code:
   ```
   /generate-changelog
   ```
   Or directly from a shell:
   ```bash
   bash ~/.claude/skills/generate-changelog/changelog.sh
   ```

## Usage

```bash
bash changelog.sh                    # write/update ./CHANGELOG.md (since last tag)
bash changelog.sh --stdout           # print to stdout, don't write
bash changelog.sh --from v1.0.0      # commits since v1.0.0
bash changelog.sh --to HEAD          # commits up to ref
bash changelog.sh --version v1.2.0   # heading version (default: "Unreleased")
bash changelog.sh --output NOTES.md  # write to a different file
bash changelog.sh --all              # full changelog across all tags
```

## Sample output

Generated against this repo (see `sample-output.md` for the full file):

```markdown
# Changelog

All notable changes to this project are documented here.

## [Unreleased] - 2026-05-10

### Added
- **skill:** add generate-changelog skill with bash script ([`abc1234`](...))

### Changed
- **docs:** update README with bounty entry ([`def5678`](...))

### Fixed
- handle empty git history without crashing ([`9012abc`](...))
```

## Categorization rules

| Commit prefix                                                 | Section            |
| ------------------------------------------------------------- | ------------------ |
| `feat:` / `feature:`                                          | Added              |
| `fix:` / `bugfix:` / `hotfix:`                                | Fixed              |
| `perf:` `refactor:` `style:` `docs:` `build:` `ci:` `chore:` `test:` | Changed     |
| `revert:`                                                     | Removed            |
| Any commit with `!` after type or `BREAKING CHANGE:` in body  | Breaking Changes (called out) |
| Non-conventional subjects                                     | Heuristic, else `Other` |

## Requirements

- `bash` 4+ (or 3.2 with the script as-is — uses portable arrays)
- `git` 2.x
- Run from inside a git working tree

## License

MIT
