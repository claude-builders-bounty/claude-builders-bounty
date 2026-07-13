# git-changelog Generator

A tiny, dependency-free tool that turns your git history into a structured `CHANGELOG.md`.

## Setup (3 steps)

1. Drop `changelog.py` (and optionally `changelog.sh`) into your repo or anywhere on disk.
2. Ensure `git` and `python3` are installed (both are standard on macOS/Linux).
3. Run it from inside any git repo:

```bash
python3 changelog.py
# or
bash changelog.sh
```

That's it. No install, no pip, no config.

## What it does

- Reads commits **since the last git tag** (`git describe --tags --abbrev=0`).
  If your repo has no tags yet, it uses the full history from the first commit.
- Categorizes each commit by its message prefix:
  - `feat` / `add` / `new` → **Added**
  - `fix` / `bug` / `resolve` / `patch` → **Fixed**
  - `remove` / `rm` / `delete` / `drop` → **Removed**
  - anything else → **Changed**
- Writes a clean `CHANGELOG.md` to the repo root (or a path you pass as the first arg).

## Claude Code skill

The included `SKILL.md` lets Claude Code generate a changelog via the `/generate-changelog` command. Drop it in your project's `.claude/skills/generate-changelog/SKILL.md`.

## Example output

```markdown
# Changelog

## [2026-07-13] - my-project
_since tag v0.1.0_

### Added
- feat: add CSV export (a1b2c3d)

### Fixed
- fix: handle null config (e4f5g6h)
```

## License

MIT — do what you want, keep the notice.
