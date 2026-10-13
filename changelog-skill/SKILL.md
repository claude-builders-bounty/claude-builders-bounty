---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks to create or update a changelog, release notes, or "what changed since the last tag". Collects commits since the most recent git tag, categorizes them into Added/Fixed/Changed/Removed, and writes a Keep-a-Changelog style file.
---

# Generate CHANGELOG from git history

Turn git history into a structured `CHANGELOG.md` with four sections:
**Added**, **Fixed**, **Changed**, **Removed**.

## When to use

- The user asks for a changelog, release notes, or "what changed since v1.2.0".
- Preparing a release and the changelog is missing or stale.
- Audit trail of changes for a repo without a manual changelog.

## How to run

```bash
bash changelog.sh                     # since the last tag, section "Unreleased"
bash changelog.sh --version v1.3.0    # name the section
bash changelog.sh --since v1.2.0      # explicit range start
bash changelog.sh --out docs/CHANGELOG.md
bash changelog.sh --dry-run           # preview on stdout, write nothing
```

## Behavior

1. Range start = `--since` if given, else the newest tag (`git describe --tags --abbrev=0`),
   else the whole history.
2. Merge commits are skipped.
3. Each commit lands in exactly one section:
   - conventional types: `feat|feature|add` → Added, `fix|bugfix|hotfix` → Fixed,
     `remove|revert|drop|delete|deprecate` → Removed, everything else
     (`refactor|perf|docs|chore|style|test|build|ci|update|bump|rename|move`) → Changed;
   - scopes and breaking-change marks are understood: `feat(api)!: drop v1` → Added;
   - free-form subjects fall back to keyword heuristics (`fix`, `add`, `remove`, ...);
   - unmatched commits go to **Changed** so nothing is silently dropped.
4. Output follows Keep a Changelog: header, range note, `## [version] - date`,
   then only the non-empty sections.

## Determinism and safety

- Read-only on the repository: the only file written is the output changelog.
- No network access, no API keys, no commits, no pushes.
- Exit codes: `0` OK, `1` bad usage, `2` not a git repository.

## Example output

See `SAMPLE-OUTPUT.md` — real output on `claude-builders-bounty/claude-builders-bounty`
and `sindresorhus/p-limit`.

## Tests

```bash
bash tests/test_changelog.sh   # 10 assertions, exit 0 = pass
```
