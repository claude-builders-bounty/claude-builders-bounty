# Generate a structured CHANGELOG from Git history

A dependency-light Bash utility that reads commit subjects since the latest reachable Git tag and writes a categorized `CHANGELOG.md`. Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `docs:`, `remove:` and related forms) map into **Added**, **Fixed**, **Changed**, and **Removed**. Subjects that do not match a known prefix are retained under **Changed (uncategorized)** rather than silently discarded.

## Requirements

- Git
- Bash 4+
- Python 3 (used only to safely split Git's NUL-delimited output)

## Setup and use (3 steps)

1. Copy `changelog.sh` into your repository, or clone this repository.
2. Run `bash changelog.sh` from the target repository. To select a tag explicitly, run `bash changelog.sh --since v1.2.3`; use `--repo PATH` and `--output PATH` to target another repository or output file.
3. Review `CHANGELOG.md` before publishing; commit subjects are heuristically categorized and may need human correction.

## Example

Given commits `feat: add CSV export`, `fix: handle empty input`, `docs: explain setup`, and `remove: legacy endpoint` since tag `v1.2.0`, the generated file includes:

```markdown
# Changelog

Changes since `v1.2.0`.

## Added

- feat: add CSV export

## Fixed

- fix: handle empty input

## Changed

- docs: explain setup

## Removed

- remove: legacy endpoint
```

If the repository has no reachable tags, all commits reachable from `HEAD` are considered. Merge commits are excluded by Git's default `git log` behavior only when requested; this script uses the normal log history. The tool does not push, tag, commit, or publish changes.
