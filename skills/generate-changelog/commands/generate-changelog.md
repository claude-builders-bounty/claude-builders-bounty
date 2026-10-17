---
description: Generate a categorized CHANGELOG.md from git history since the last tag
allowed-tools: Bash, Read, Edit
---

# Generate a changelog

Run the changelog generator from the repo root, covering every commit since the last git tag.
Commits are categorized into Added / Fixed / Changed / Removed.

First inspect the scope so you can report it, then run the generator:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "(no tags)"
```

```bash
python3 ~/.claude/skills/generate-changelog/changelog.py --version "$1" --dry-run
```

If the dry run looks right, write it:

```bash
python3 ~/.claude/skills/generate-changelog/changelog.py --version "$1"
```

Then summarize for the user: how many commits were categorized, the version heading used,
and any commit that landed in the `Changed` bucket because no category was detected.

Arguments: `$1` is the version heading (e.g. `1.4.0`). If omitted, defaults to `Unreleased`.
