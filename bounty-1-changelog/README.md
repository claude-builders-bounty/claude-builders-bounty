# Bounty 1 — Generate CHANGELOG from Git History

A Claude Code skill that generates a formatted CHANGELOG from your git commit history.

## Setup (2 steps)

1. Copy `changelog.sh` into your project (or reference it by path)
2. Run it:
   ```bash
   bash changelog.sh
   ```

## What it does

| Step | Description |
|------|-------------|
| **Detect range** | Finds the latest git tag as the start point. Falls back to the repo root if no tags exist. |
| **Collect commits** | Reads all commits between the start ref and HEAD. |
| **Categorize** | Sorts each commit into Added / Fixed / Changed / Removed using conventional commit prefixes, then keyword fallback. |
| **Format** | Outputs clean Markdown following [Keep a Changelog](https://keepachangelog.com) conventions. |

## How it works

**Categorization priority:**

1. **Conventional commits** — `feat:` → Added, `fix:` → Fixed, `remove:`/`revert:` → Removed, everything else → Changed
2. **Keyword fallback** — scans the commit message for words like "add", "fix", "remove", "delete", "implement"
3. **Default** — anything uncategorized lands in Changed

**Prefix stripping** — conventional commit prefixes (`feat(scope): ...`) are stripped from the display for cleaner output.

## Options

```
--from <ref>       Start ref (default: latest git tag)
--to <ref>         End ref (default: HEAD)
--output <file>    Write to file instead of stdout
--version <ver>    Version label (default: Unreleased)
```

## Examples

```bash
# Basic usage — prints to stdout
bash changelog.sh

# Write to file with version label
bash changelog.sh --version "1.2.0" --output CHANGELOG.md

# Custom range
bash changelog.sh --from v1.0.0 --to v1.1.0

# From a specific commit
bash changelog.sh --from abc1234
```

## As a Claude Code Skill

See [SKILL.md](SKILL.md) for installation as a `/generate-changelog` slash command.

## Sample output

See [samples/sample-output.md](samples/sample-output.md).
