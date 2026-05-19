---
name: generate-changelog
description: >-
  Generate a structured CHANGELOG.md from git history. Fetches commits since the
  last git tag, auto-categorizes by Conventional Commits (feat → Added, fix → Fixed,
  refactor/perf → Changed, revert → Removed), and outputs a formatted Markdown file.
tags:
  - changelog
  - git
  - conventional-commits
  - release
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from git history using Conventional Commit
prefixes to auto-categorize entries.

## Usage

```
/generate-changelog
```

To specify a starting ref or version:

```
/generate-changelog --since v1.0.0 --version v2.0.0
```

To preview without writing:

```
/generate-changelog --dry-run
```

## How It Works

When invoked, run the script:

```bash
bash changelog.sh $@
```

The script will:

1. Detect the latest git tag (or first commit if no tags exist)
2. Fetch all commits since that reference
3. Parse each commit subject for Conventional Commit prefixes:
   - `feat:` / `feat(...):` → **Added**
   - `fix:` / `fix(...):` → **Fixed**
   - `refactor:` / `perf:` / `style:` → **Changed**
   - `revert:` → **Removed**
   - `docs:` / `test:` / `chore:` / `ci:` → **Other**
4. Group entries under the appropriate section
5. Write `CHANGELOG.md` with the new release prepended at the top

## Flags

| Flag | Description |
|------|-------------|
| `--since`, `-s` | Git ref to start from (default: latest tag) |
| `--version`, `-v` | Version string for header (default: latest tag) |
| `--output`, `-o` | Output file path (default: CHANGELOG.md) |
| `--dry-run`, `-n` | Print to stdout without writing |
