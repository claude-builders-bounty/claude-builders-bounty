---
name: changelog
description: Generate a Keep-a-Changelog style CHANGELOG from git commits since the last tag (Added / Fixed / Changed / Removed).
---

# Changelog skill

When the user asks for a changelog, release notes, or commits-since-last-tag summary:

1. Run `bash changelog.sh` from the repo root (script lives next to this skill or at repo root).
2. Write or update `CHANGELOG.md` with the script output.
3. Keep sections: Added, Fixed, Changed, Removed.

## Script

```bash
bash changelog.sh [optional/path/to/repo]
```

Classifies conventional commit prefixes (`feat:`, `fix:`, `chore:`, `remove:`, etc.) and simple keyword heuristics into Keep-a-Changelog groups.
