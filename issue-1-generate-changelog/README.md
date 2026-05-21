# Generate a structured changelog from git history

This package solves issue #1 with a portable Python script that reads commits since the latest git tag and writes a categorized `CHANGELOG.md`.

## Use in 3 steps

```bash
cd your-git-repo
python path/to/changelog.py --output CHANGELOG.md
cat CHANGELOG.md
```

Optional preview without writing:

```bash
python path/to/changelog.py --stdout
```

## Categories

- `Added`: commits that look like new features, additions, or creations.
- `Fixed`: commits that look like bug fixes, repairs, or corrections.
- `Changed`: commits that look like updates, refactors, docs, tests, CI, chores, or releases.
- `Removed`: commits that look like removals, deletions, or deprecations.

## Tag behavior

The script detects the latest reachable tag with:

```bash
git describe --tags --abbrev=0
```

If no tag exists, it falls back to all reachable commits.

## Files

- `changelog.py`: changelog generator.
- `sample-output.md`: sample output generated from a real repository.
