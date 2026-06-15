# generate-changelog

Claude Code skill for generating structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `changelog.py` to your project root
2. Run `python3 changelog.py`
3. Commit the generated `CHANGELOG.md`

## Usage

```bash
# Generate changelog since last tag
python3 changelog.py

# Specify output file
python3 changelog.py --output CHANGELOG.md

# Specify version string
python3 changelog.py --version "v1.2.0"
```

## Requirements

- Python 3.8+
- Git repository with at least one tag

## Sample Output

See `CHANGELOG.md` in this repo for sample output.
