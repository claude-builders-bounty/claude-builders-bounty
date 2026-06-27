---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history
command: /generate-changelog
trigger: ""
---

# Generate CHANGELOG

Fetches commits since the last git tag, auto-categorizes into
**Added** / **Fixed** / **Changed** / **Removed**, and outputs
a properly formatted `CHANGELOG.md`.

## Usage

```bash
/generate-changelog
```

Or with a custom range:

```bash
/generate-changelog --from v1.0.0 --to HEAD
```

## How it works

1. Finds the most recent git tag reachable from `HEAD`
2. Gathers all non-merge commits since that tag
3. Categorizes each commit using:
   - **Conventional Commit prefixes** (`feat:` → Added, `fix:` → Fixed, etc.)
   - **Keyword fallback** (`add`, `fix`, `remove`, …)
4. Suggests the next patch version based on the last tag
5. Outputs a well-formatted Markdown file with commit links

## Files created

- `CHANGELOG.md` — the generated changelog in the project root

## Requirements

- `git` 2.x+
- `bash` 4.x+
