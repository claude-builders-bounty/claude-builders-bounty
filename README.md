# generate-changelog

Generate a structured `CHANGELOG.md` from your git history, grouped into
**Added / Fixed / Changed / Removed** (Keep a Changelog 1.1.0 format).

Works with conventional commits and falls back to heuristics for repos that
don't follow the convention. No external dependencies — just `bash`, `git`,
and `awk`.

## Setup (3 steps)

1. Copy `changelog.sh` into your repo (e.g. `./scripts/changelog.sh`).
2. Add `SKILL.md` to your Claude Code skills directory (`~/.claude/skills/generate-changelog/SKILL.md`).
3. Run `bash scripts/changelog.sh` from your repo root. A `CHANGELOG.md` will be created (or prepended) automatically.

## Usage

```bash
# Default: changelog since the most recent git tag
bash changelog.sh

# Explicit range
bash changelog.sh --since v1.0.0

# Explicit version
bash changelog.sh --version 2.0.0

# Preserve an existing [Unreleased] block
bash changelog.sh --keep-unreleased

# Bypass clean-tree check
bash changelog.sh --allow-dirty
```

In Claude Code, just type:

```
/generate-changelog
```

…and the skill will detect the range and write the file.

## What it does

1. Detects the range: `--since <ref>` → most recent tag → all non-merge commits.
2. Collects commits (`git log` with `%H %an %ae %aI %s`).
3. Categorizes each subject by conventional-commit prefix:
   - `feat`/`feature`/`add`/`new` → **Added**
   - `fix`/`bug`/`patch`/`hotfix` → **Fixed**
   - `refactor`/`perf`/`docs`/`chore`/`build`/`ci` → **Changed**
   - `remove`/`drop`/`deprecate` → **Removed**
4. Falls back to a first-verb heuristic when no conventional prefix is found.
5. Marks `BREAKING CHANGE` / `!` commits into a top **⚠️ BREAKING CHANGES** section.
6. Writes a Keep-a-Changelog 1.1.0 section; preserves prior content.

## Output

```markdown
## [1.2.1] - 2026-08-01

### Added
- feat(api): add /healthz endpoint (a1b2c3d)
- feat: support --since date ranges (e9f8g7h)

### Fixed
- fix(cli): handle missing tag gracefully (1a2b3c4)

### Changed
- refactor: extract categorization to awk (5d6e7f8)
```

See [`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md) for a real run against a public repo.

## License

MIT — matches the parent `claude-builders-bounty` repository.
