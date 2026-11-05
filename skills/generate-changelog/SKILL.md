---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history since the last git tag, auto-categorizing commits into Added / Fixed / Changed / Removed. Use when the user asks to create or update a changelog, summarize recent changes, or runs the /generate-changelog command.
---

# Generate a structured CHANGELOG

This skill generates a `CHANGELOG.md` from the current git repository's history
**since the last tag**, categorizing each commit into
**Added / Fixed / Changed / Removed** (Keep a Changelog format).

Zero dependencies: only `bash` + `git`. Works on macOS (bash 3.2) and Linux.

## When to use
- The user says "generate a changelog", "update CHANGELOG", "summarize changes since last release", or invokes `/generate-changelog`.
- They want a release-notes style summary without manual writing.

## How to run

The skill ships a zero-dependency `changelog.sh`. Run it from the project root:

```bash
# Default: writes CHANGELOG.md in the current repo (uses last tag as the start point)
bash skills/generate-changelog/changelog.sh

# Common options
bash skills/generate-changelog/changelog.sh --repo . --output CHANGELOG.md
bash skills/generate-changelog/changelog.sh --since-tag v1.2.0 --version v1.3.0
bash skills/generate-changelog/changelog.sh --dry-run        # print to stdout only
```

If the repo has **no tags**, the script gracefully falls back to the full history
and notes this in the output.

## What it does
1. Detects the most recent tag via `git describe --tags --abbrev=0`
   (or use `--since-tag` to override).
2. Reads commits in `${last_tag}..HEAD` (merge commits excluded).
3. Classifies each commit:
   - **Conventional Commits** prefix: `feat:`→Added, `fix:`→Fixed,
     `refactor:`/`perf:`/`chore:`/`build:`/`ci:`→Changed, `remove:`→Removed, …
   - **Chinese keyword** fallback: `新增/添加`→Added, `修复/修正`→Fixed,
     `删除/移除`→Removed, `重构/优化/改进`→Changed.
   - Unmatched commits default to **Changed** (never dropped).
4. Writes a Keep a Changelog formatted `CHANGELOG.md`.

## Output
A file like:

```markdown
## [Unreleased] - 2026-11-05

自 tag `v0.1.0` 之后的提交（共 7 条提交）。

### Added
- feat: 新增 CSV 批量清洗与重复行检测 (203dbb0)

### Fixed
- fix: 修复命令防火墙在 zsh 下的引号解析错误 (a3caadd)
```

A sample produced from a real GitHub repository is in `examples/SAMPLE_CHANGELOG.md`.
