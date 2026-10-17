---
name: generate-changelog
description: Generate a categorized CHANGELOG.md from git history. Use when the user asks to write or update a changelog, draft release notes, or asks "what changed since the last release". Categorizes commits into Added / Fixed / Changed / Removed.
---

# generate-changelog

Turns git history into a Keep-a-Changelog file. Usable two ways: the `/generate-changelog`
command, or `bash changelog.sh` directly.

## When to use

- "write a changelog", "update CHANGELOG.md", "draft release notes", "what changed since v1.2.0".
- Cutting a release and needing the since-last-tag commits sorted by category.

## Steps

1. Establish the range first, so you can report it honestly:

   ```bash
   git describe --tags --abbrev=0 2>/dev/null || echo "(no tags — walking full history)"
   ```

2. Preview it — nothing is written:

   ```bash
   python3 ~/.claude/skills/generate-changelog/changelog.py --version "${1:-Unreleased}" --dry-run
   ```

3. If the preview looks right, write it:

   ```bash
   python3 ~/.claude/skills/generate-changelog/changelog.py --version "${1:-Unreleased}"
   ```

4. Report back: how many commits were categorized, which heading was used, and any commit that
   landed in `Changed` because no category was detected.

## Flags

| Flag | Effect |
|---|---|
| `--from <ref>` / `--to <ref>` | explicit range instead of since-last-tag |
| `--dry-run` | print the changelog, write nothing |
| `--version <v>` | heading for the new section (default `Unreleased`) |

## Notes

- Run from the repo root. Output is `./CHANGELOG.md`.
- Merge commits are skipped. An unmatched commit lands in `Changed` rather than being dropped.
- Re-running prepends the new section above the previous, so the file stays newest-first.
- Conventional prefixes are stripped and scopes preserved: `feat(auth): add OAuth` →
  `- **auth:** add OAuth (cace3e0)`.

## Install

```bash
cp -r . ~/.claude/skills/generate-changelog/
cp commands/generate-changelog.md ~/.claude/commands/
```
