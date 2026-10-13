# Generate Changelog

## Description
Automatically generates a structured `CHANGELOG.md` from git commit history using conventional commit prefixes.

## Usage
```bash
# Generate CHANGELOG.md (default output)
bash changelog.sh

# Specify custom output file
bash changelog.sh CHANGELOG.md
```

## What it does
1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes commits into `Added`, `Fixed`, `Changed`, or `Removed` based on commit message prefixes
3. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format

## Commit Prefixes
- `feat:`, `add:`, `new:`, `implement:`, `introduce:` → **Added**
- `fix:`, `bug:`, `patch:`, `resolve:`, `correct:`, `repair:` → **Fixed**
- `remove:`, `delete:`, `drop:`, `deprecate:` → **Removed**
- `update:`, `change:`, `modify:`, `refactor:`, `improve:`, `enhance:`, `upgrade:`, `bump:` → **Changed**
- Everything else → **Changed**

## Setup (3 steps)
1. Copy `changelog.sh` to your project
2. Run `bash changelog.sh`
3. Review the generated `CHANGELOG.md`

## Requirements
- Git 2.0+
- Bash 4.0+
