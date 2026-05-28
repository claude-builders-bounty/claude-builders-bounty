# generate-changelog

A Claude Code skill and standalone Python script that automatically generates
a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

**Step 1** — Place `changelog.py` and `changelog.sh` in your project.

```bash
cp changelog.py changelog.sh /path/to/your/project/
chmod +x changelog.sh
```

**Step 2** — Generate your changelog.

```bash
cd /path/to/your/project && bash changelog.sh -o CHANGELOG.md
```

**Step 3** — (Optional) Install as a Claude Code skill by placing `SKILL.md`
in `.claude/skills/`:

```bash
cp SKILL.md /path/to/your/project/.claude/skills/generate-changelog.md
```

Then run `/generate-changelog` inside a Claude Code session.

---

## Requirements

- **Python 3.8+**
- **Git 2.20+**
- A repository that uses [Conventional Commits](https://www.conventionalcommits.org/)
  (works without them — unrecognized commits go under Changed)

## Options

```
usage: changelog.py [-h] [--since SINCE] [--until UNTIL] [--output OUTPUT]
                    [--version VERSION] [--repo REPO] [--date DATE]

Generate a structured CHANGELOG.md from git history.

optional arguments:
  -h, --help            show this help message and exit
  --since SINCE, -s SINCE
                        Tag name or ISO date (YYYY-MM-DD). Default: last tag.
  --until UNTIL, -u UNTIL
                        End date for date-range filtering.
  --output OUTPUT, -o OUTPUT
                        Output file path. Default: stdout.
  --version VERSION, -v VERSION
                        Version string for heading (default: Unreleased).
  --repo REPO, -r REPO  Path to git repo (default: current dir).
  --date DATE, -d DATE  Release date (YYYY-MM-DD). Default: today.
```

## Example Output

```markdown
# Changelog

## 1.2.0 — 2025-06-15

### Added

- Support for date-range filtering (`--since` / `--until`)
- Auto-detection of breaking changes from `BREAKING CHANGE` footers
- `--repo` flag to target a different repository

### Fixed

- Edge case where empty commit body caused index errors
- Commit message encoding for non-ASCII characters

### Changed

- Improved categorization for `perf:` and `optimize:` prefixes
- Better indentation for multi-line commit bodies

## License

MIT
