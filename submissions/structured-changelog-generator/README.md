# Changelog generator

Generate a structured `CHANGELOG.md` from git history, with no third-party dependencies.

## 3-step setup

1. Copy `changelog.py` (and optionally `changelog.sh`) into your project.
2. Run `python3 changelog.py --repo . --output CHANGELOG.md`.
3. Commit the generated `CHANGELOG.md`.

## Usage

```bash
# local repository, automatically since the latest tag
python3 changelog.py --repo . --output CHANGELOG.md

# choose a start tag
python3 changelog.py --repo . --since-tag v1.4.0

# no local clone? use GitHub API
python3 changelog.py --github psf/requests --output CHANGELOG.md
```

If `--since-tag` is omitted, the script uses the latest tag (`git describe --tags --abbrev=0`); if there is no tag, it uses the full history (local) or the latest 100 commits (GitHub API).

## Categories

- **Added**: `feat:`, `add ...`, `new ...`, `implement ...`, `introduce ...`
- **Fixed**: `fix:`, `bugfix:`, `hotfix:`, `resolve ...`, `correct ...`
- **Changed**: `refactor:`, `perf:`, `docs:`, `chore:`, `update ...`, `improve ...`
- **Removed**: `remove ...`, `delete ...`, `drop ...`, `deprecate ...`
- **Other**: anything else

## Notes

- Merge commits are skipped in local mode.
- GitHub API mode needs no token for light use; set `GITHUB_TOKEN` to avoid rate limits.
- Output includes the commit link when available.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
