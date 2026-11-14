---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped into Added/Fixed/Changed/Removed/Other.
---

# /generate-changelog

When the user invokes `/generate-changelog` (or asks for a changelog from git history):

1. Detect the repository root (`git rev-parse --show-toplevel`).
2. Run:
   ```bash
   python3 changelog.py --repo . --output CHANGELOG.md
   ```
3. Read the generated file and summarize what changed for the user.
4. If the repo has no tags, the script uses full history; mention that.
5. If running outside a git repo, ask for a `--github owner/repo` target or a repo path.

Always show the generated file path and the number of commits included.
