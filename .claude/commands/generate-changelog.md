---
description: Generate or update CHANGELOG.md from git history since the last tag
allowed-tools: Bash(git *), Bash(python *), Read, Write, Edit
---

Run the bundled generator and polish the result:

1. `python .claude/skills/generate-changelog/generate_changelog.py -o CHANGELOG.md`
2. Read `CHANGELOG.md`, rewrite any awkward commit subjects into clear release-note prose.
3. Reply with a short summary of what landed under each category.

If the user passed arguments in `$ARGUMENTS`, forward them to the script
(e.g. `--since v1.2.0`).
