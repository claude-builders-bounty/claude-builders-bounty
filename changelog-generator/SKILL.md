---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

When the user asks for `/generate-changelog`, run:

```bash
bash changelog.sh
```

If `changelog.sh` is not present in the current repository, copy this skill bundle's script into the repository root first.

After generation:

1. Report the tag range used.
2. Summarize how many commits were categorized.
3. Ask the user to review `CHANGELOG.md` before release.
