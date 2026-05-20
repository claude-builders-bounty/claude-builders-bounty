---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a structured `CHANGELOG.md` generated from its Git history.

## Command

Run the repository script from the project root:

```bash
bash changelog.sh
```

To write to another path, pass the output file as the first argument:

```bash
bash changelog.sh /tmp/CHANGELOG.md
```

## What It Does

The script finds commits since the latest Git tag. If the repository has no tags, it uses the full history.

It ignores merge commits, categorizes commit subjects into these sections, and writes a Markdown changelog:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

## Review Checklist

After running the command, verify that:

- `CHANGELOG.md` exists at the expected path
- commits are grouped under the four supported headings
- the generated range matches the latest tag or the full history when no tag exists
