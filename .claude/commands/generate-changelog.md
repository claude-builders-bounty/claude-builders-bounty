---
description: Generate a structured CHANGELOG.md from git history.
allowed-tools: Bash
---

Run the changelog generator from the repository root:

```bash
bash changelog.sh
```

The script reads commits since the latest git tag, groups them into Added, Fixed, Changed, and Removed, and writes the result to `CHANGELOG.md`.
