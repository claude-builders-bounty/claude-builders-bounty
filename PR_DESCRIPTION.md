# Summary

Implements bounty #1 with a reusable changelog generator:

- Adds `scripts/changelog.sh` for generating a structured `CHANGELOG.md` from git history.
- Adds a Claude Code skill wrapper in `skills/generate-changelog/SKILL.md`.
- Adds 3-step setup/use documentation in `CHANGELOG_GENERATOR.md`.
- Adds a sample output generated from this repository's git history.

# Verification

```bash
bash -n scripts/changelog.sh
bash scripts/changelog.sh --output /tmp/generated-changelog.md
git diff --check
```

Sample output is included at `samples/sample-CHANGELOG.md`.

Closes #1.
