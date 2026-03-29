# generate-changelog

Generate a structured `CHANGELOG.md` from git history in seconds.

## Setup

```bash
git clone https://github.com/leegier/generate-changelog
python generate_changelog.py
```

## Usage

```bash
python generate_changelog.py              # since last tag
python generate_changelog.py v1.2.0       # since specific tag
python generate_changelog.py v1.2.0 v1.3.0  # between two tags
bash changelog.sh                         # bash wrapper
```

## Requirements
- Python 3.8+
- Git
