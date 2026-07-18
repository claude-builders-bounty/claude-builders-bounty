# changelog-generator skill

A Claude Code skill that produces a Keep-a-Changelog `CHANGELOG.md` straight from
your git history.

## Setup (3 steps)

```bash
# 1. Drop the skill folder into your repo's skills/ directory
mkdir -p skills
cp -R skills/changelog-generator skills/

# 2. Make the executable findable
chmod +x skills/changelog-generator/changelog.py

# 3. Run it — either as a slash command from Claude Code or directly:
python3 skills/changelog-generator/changelog.py --since-tag v1.0.0
```

That's it. The script needs only Python 3.8+ and `git` (already on PATH for any
working repo).

## What you get

A `CHANGELOG.md` that looks like:

```markdown
# Changelog

All recorded changes for <your-project>.

_Generated on 2026-07-18 22:00 UTC_

## Added
- new dashboard widget (`a1b2c3d4`, alice, 2026-07-12T09:14:30+00:00)
- support for custom plugins (`f9e8d7c6`, bob, 2026-07-14T17:02:11+00:00)

## Fixed
- race condition in worker queue (`12ab34cd`, alice, 2026-07-15T08:44:01+00:00)

## Changed
- refactor API client to use httpx (`9f8e7d6c`, carol, 2026-07-13T19:50:22+00:00)
```

See `SAMPLE_CHANGELOG.md` for a real run on a public repo.

## Why this exists

Editing `CHANGELOG.md` by hand is fine for one release a month. Three PRs a
day later, you stop. This script regenerates the whole file from `git log`
in under a second and keeps it in CI without a round-trip through a human.

## License

MIT.
