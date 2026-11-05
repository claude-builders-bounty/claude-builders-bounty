# generate-changelog

Generate a structured `CHANGELOG.md` from your git history — commits since the last
tag, auto-categorized into **Added / Fixed / Changed / Removed**.

## Setup (3 steps)
1. Add this folder to your project (or copy `generate_changelog.py`).
2. (optional) `chmod +x generate_changelog.py`
3. Run:
   ```bash
   python3 generate_changelog.py           # writes CHANGELOG.md
   python3 generate_changelog.py --version 1.2.0
   ```
   Bash alternative: `bash changelog.sh`

## Claude Code skill
Copy `SKILL.md` into your skills directory and run `/generate-changelog`.

## Tests
```bash
python3 -m unittest discover -s tests -v   # 6 tests, stdlib only
```

## Requirements
`git` + Python 3.9+ (or bash). No third-party packages.

## Sample
See [`examples/SAMPLE_CHANGELOG.md`](examples/SAMPLE_CHANGELOG.md).
