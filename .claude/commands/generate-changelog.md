---
description: Generate a structured CHANGELOG.md from git history
allowed-tools: Bash
---

Generate or refresh a structured changelog for this repository.

Run:

```bash
bash changelog.sh
```

Then review `CHANGELOG.md` and summarize:

- the detected previous tag or fallback history range
- the number of entries in Added, Fixed, Changed, and Removed
- any commits that may need manual recategorization

If the user provides arguments, pass them through to the script. Examples:

```bash
bash changelog.sh --from v1.2.0
bash changelog.sh --output docs/CHANGELOG.md --from v1.2.0 --to HEAD
```
