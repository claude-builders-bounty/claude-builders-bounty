---
description: Generate a structured CHANGELOG.md from git commits since the last tag
disable-model-invocation: false
allowed-tools: Bash(bash *) Bash(git *) Read
---

# /generate-changelog

Generate a Keep-a-Changelog-style `CHANGELOG.md` from this repository's git history.

## Steps

1. Run the generator from the project root (or the path of this skill's sibling script):

```bash
bash ${CLAUDE_PROJECT_DIR}/beamo-changelog/changelog.sh --replace
```

If this skill was installed under `~/.claude/skills/generate-changelog/`, use:

```bash
bash ~/.claude/skills/generate-changelog/changelog.sh --replace
```

2. Read the resulting `CHANGELOG.md` and briefly summarize the Added / Fixed / Changed / Removed sections for the user.

3. If there are no commits since the last tag, say so clearly and do not invent entries.
