# Generate Changelog

## Setup (1 step)
```bash
cp generate-changelog/changelog.sh .
bash changelog.sh
```

## What you get
A `CHANGELOG.md` with categorized commits, PR references, and tag links.

## Tested on
- [korpo1337/korpo](https://github.com/korpo1337/korpo) — 4 commits, auto-categorized correctly
- Fresh repo without tags — falls back to all commits
