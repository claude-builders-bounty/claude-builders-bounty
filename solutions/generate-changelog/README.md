# Automatic Changelog Generator

Generates a `CHANGELOG.md` in the repository root from Git commit subjects after the latest reachable tag (as selected by `git describe --tags --abbrev=0`). Commits are categorized as **Added**, **Fixed**, **Changed**, or **Removed**, with short commit hashes. Without any tags, all non-merge commits are included. Merge commits are excluded. The script requires Bash 4+ and Git; no API keys, additional dependencies, or network connection are necessary.

## Setup (3 steps)

1. Download `changelog.sh` into your Git repository (or clone this project).
2. Run `bash changelog.sh` from inside the Git repository, or `bash changelog.sh /path/to/repo`.
3. Open the generated `CHANGELOG.md` in that repository.

## Example

Given a repository tagged `v1.0.0` followed by commits `feat: add invoice export`, `fix: prevent duplicate uploads`, `remove: legacy endpoint`, `docs: clarify setup`, the output contains:

```markdown
# Changelog

## Changes since v1.0.0

### Added

- feat: add invoice export (`<hash>`)

### Fixed

- fix: prevent duplicate uploads (`<hash>`)

### Changed

- docs: clarify setup (`<hash>`)

### Removed

- remove: legacy endpoint (`<hash>`)
```

The file is rewritten on each successful run to avoid duplicated entries. Back up any hand-written notes before running it. Conventional Commit prefixes support optional scopes and breaking-change markers, for example `feat(api):`, `fix(parser):`, `feat!:`, and `fix(parser)!:`. `feat` maps to Added, `fix`/`bugfix` to Fixed, and `remove`/`delete` to Removed. Readable verbs such as `Added`, `Fixed`, and `Drop` are also recognized, case-insensitively. All other commit subjects fall under Changed.

A repository without commits is an error and does not create or overwrite `CHANGELOG.md`. Git history read failures also preserve the existing file and return a nonzero status. A tag at `HEAD` is valid and produces empty sections.

## Tests

Run `bash solutions/generate-changelog/test.sh` from this project's root. The dependency-free suite creates temporary Git repositories and checks categorization, tags, repeatability, subdirectory invocation, empty/invalid/bare repositories, and a simulated Git history read failure.

## Verified on GitHub repository
The included `SAMPLE_CHANGELOG.md` was generated on the real public `claude-builders-bounty/claude-builders-bounty` history at commit `1aeae2adc82d33f971fd7731644348dcdd24b5a6`. Reproduce it from a clone with:

```bash
git worktree add --detach /tmp/changelog-sample 1aeae2adc82d33f971fd7731644348dcdd24b5a6
bash solutions/generate-changelog/changelog.sh /tmp/changelog-sample
diff -u solutions/generate-changelog/SAMPLE_CHANGELOG.md /tmp/changelog-sample/CHANGELOG.md
```

Use a fresh destination path if `/tmp/changelog-sample` already exists. No secrets or API access are needed to run the generator.
