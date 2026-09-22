---
description: Generate a structured CHANGELOG.md from git history (Added/Changed/Fixed/Removed).
---

Generate a structured changelog for this repository.

Run the bundled script and write the result to `CHANGELOG.md`:

```bash
bash changelog.sh -o CHANGELOG.md
```

If `changelog.sh` is not in the repo root, use the path where it was installed
(e.g. `skills/changelog-generator/changelog.sh`).

The script:
- collects commits since the most recent git tag (or full history if none),
- categorises them into **Added / Changed / Fixed / Removed** using
  Conventional-Commit prefixes and keyword heuristics,
- writes/prepends a Keep-a-Changelog formatted block.

After running, show the user the top of the generated `CHANGELOG.md` and offer
to adjust the version header (`--version x.y.z`) or the starting ref
(`--since <tag>`) if needed.
