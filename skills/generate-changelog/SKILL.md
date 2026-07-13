---
name: generate-changelog
description: Generate a Keep a Changelog-style CHANGELOG.md from Git commits since the latest reachable tag. Use when the user asks to create, refresh, preview, or automate a project changelog.
---

# Generate Changelog

Generate the changelog from the repository root:

```bash
bash "${CLAUDE_SKILL_DIR}/changelog.sh" --repo "$PWD"
```

Before running, confirm the current directory is the intended Git repository. The script:

- selects commits after the latest tag reachable from `HEAD`, or the full history when no tag exists;
- excludes merge commits;
- maps conventional commit types and common subject prefixes into exactly `Added`, `Fixed`, `Changed`, and `Removed`;
- writes `CHANGELOG.md` atomically so a failed run does not truncate the existing file.

Use `--output -` to preview without writing. Existing files are preserved unless the user explicitly approves replacement with `--force`. Use `--since <revision>`, `--version <label>`, or `--output <path>` only when the user requests an override. Report the selected base and commit count printed by the script.
