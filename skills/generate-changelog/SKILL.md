---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git history.
command: /generate-changelog
---

# Generate Changelog Skill

A production-ready skill that analyzes git commit history, categorizes conventional commits, and generates or prepends formatted entries into `CHANGELOG.md`.

## Slash Command

When the user runs `/generate-changelog` or asks to update the changelog:

1. **Detect Changes**: Determine the commit delta since the last release tag (or all commits if no tags exist).
2. **Execute**: Run `bash skills/generate-changelog/changelog.sh` (or `./changelog.sh`).
3. **Optional Flags**:
   - `/generate-changelog --write`: Prepend directly to `CHANGELOG.md`.
   - `/generate-changelog --version v1.0.0`: Specify release version header.
   - `/generate-changelog --all`: Parse full repository commit history.

## Conventional Commit Mapping

Commits are parsed according to standard conventional specifications:
- `feat:` / `feature:` / `add:` $\rightarrow$ **`### Added`**
- `fix:` / `bug:` / `patch:` $\rightarrow$ **`### Fixed`**
- `refactor:` / `perf:` / `style:` / `update:` $\rightarrow$ **`### Changed`**
- `remove:` / `delete:` / `revert:` $\rightarrow$ **`### Removed`**
- `sec:` / `security:` $\rightarrow$ **`### Security`**
- `chore:` / `docs:` / `build:` / `ci:` $\rightarrow$ **`### Maintenance & Chores`**

## CLI Execution Examples

```bash
# Preview changelog for changes since last tag
./changelog.sh

# Write new release entry directly into CHANGELOG.md
./changelog.sh -v "v2.1.0" -w

# Generate changelog across specific tag range
./changelog.sh --since "v2.0.0" --until "v2.1.0" -o RELEASE_NOTES.md
```
