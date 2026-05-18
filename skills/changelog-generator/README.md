# Changelog Generator

Generates a structured `CHANGELOG.md` from git history since the last tag.

## Setup (3 steps)

```bash
# 1. Make scripts executable
chmod +x skills/changelog-generator/changelog.sh

# 2. Ensure you are in a git repository
cd /your/project

# 3. Pick one method below
```

## Usage

### Bash

```bash
./skills/changelog-generator/changelog.sh
# or specify a custom output file
./skills/changelog-generator/changelog.sh HISTORY.md
```

### Python

```bash
python3 skills/changelog-generator/changelog.py
python3 skills/changelog-generator/changelog.py HISTORY.md
```

### Claude Code

```
/generate-changelog
```

## Output

Writes to `CHANGELOG.md` (or the specified filename) in the current directory.

## Verification

Run these commands to verify the scripts work on your repo:

```bash
bash skills/changelog-generator/changelog.sh /tmp/test-changelog.md
python3 skills/changelog-generator/changelog.py /tmp/test-changelog-py.md
cat /tmp/test-changelog.md
```
