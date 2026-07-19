---
name: generate-changelog
description: Generate a concise, structured CHANGELOG.md from the commits since the latest git tag. Use when a user asks to prepare release notes, summarize recent repository history, or run /generate-changelog in a Git repository.
---

# Generate Changelog

Create release notes from the current Git repository without inventing user-facing changes. The bundled script performs deterministic extraction and categorization; review the result for clarity.

## Workflow

1. Confirm the working directory is a Git repository.
2. Run `bash <skill-directory>/scripts/changelog.sh [output-path]` from the repository root. The script uses commits after the latest tag; if there is no tag, it uses all commits.
3. Review duplicates, private details, and misleading categories. Keep the original subject unless a clearer wording is obvious from the commit.
4. Show the generated file and mention the tag used as the starting point.

## Output contract

Use Keep a Changelog headings: `Added`, `Fixed`, `Changed`, and `Removed`, under an `Unreleased` section dated with the current date. Conventional prefixes are preferred; unknown commits go under `Changed`. Do not claim a security, breaking-change, or user-visible impact unless the commit supports it.

## Manual fallback

If the script cannot run, use:

```bash
latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
git log --format='%s' ${latest_tag:+"$latest_tag.."}HEAD
```

Then group the subjects into the four headings and state that the result was assembled manually.
