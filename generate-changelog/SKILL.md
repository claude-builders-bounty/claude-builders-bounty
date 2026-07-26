---
name: generate-changelog
description: >
  Generate a structured CHANGELOG.md from git history since the last tag,
  auto-categorized into Added / Fixed / Changed / Removed. Use when the user
  runs /generate-changelog, asks for a changelog from commits, or wants
  Keep-a-Changelog style release notes from git.
---

# Generate Changelog

Produce a properly formatted `CHANGELOG.md` from the repository’s git history.

## Command

```bash
# From this directory, against the current repo (or pass a path):
bash changelog.sh [output-path] [repo-path]

# Examples
bash changelog.sh
bash changelog.sh CHANGELOG.md .
bash changelog.sh /tmp/out.md /path/to/repo
```

Slash-command alias for Claude Code / Grok: **`/generate-changelog`**.

## Behavior

1. Resolve the target git repository (default: current directory).
2. Find the latest git tag (`git describe --tags --abbrev=0`). If none, use full history.
3. Collect non-merge commits in that range (`hash` + subject).
4. Categorize each subject into **Added** / **Fixed** / **Changed** / **Removed** using conventional-commit types (`feat`, `fix`, …) and keyword fallbacks (`add`, `fix`, `remove`, …).
5. Write a Keep-a-Changelog-style `CHANGELOG.md` with those four sections.

## Steps for the agent

1. Confirm the target repo path (default `.`).
2. Run `bash generate-changelog/changelog.sh CHANGELOG.md <repo>` (adjust path to this skill’s `changelog.sh`).
3. Show the user the written file and a short summary of section counts.
4. Do not invent commits — only git history is allowed.

## Acceptance mapping

| Criterion | How this skill meets it |
|-----------|-------------------------|
| `/generate-changelog` or `bash changelog.sh` | Slash name + `changelog.sh` entry point |
| Commits since last tag | `git describe --tags` + `tag..HEAD` |
| Added / Fixed / Changed / Removed | Four sections always present |
| Formatted CHANGELOG.md | Keep-a-Changelog layout |
| Real-repo sample | See `sample-CHANGELOG.md` and PR demo |
| README ≤ 3 steps | `README.md` |
