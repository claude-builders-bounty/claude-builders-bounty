---
description: Generate a structured CHANGELOG.md from git history
---

Run the repository changelog generator:

```bash
bash changelog.sh
```

If the user provides an output path, pass it as the first argument:

```bash
bash changelog.sh "$ARGUMENTS"
```

After generation, summarize which commit range was used and where the changelog
was written.
