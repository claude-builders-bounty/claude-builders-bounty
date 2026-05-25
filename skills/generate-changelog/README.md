# Generate Changelog

Generate a categorized `CHANGELOG.md` from git history.

## Setup

1. Copy `skills/generate-changelog/` into a git repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

## Usage

Write to the default file:

```bash
bash skills/generate-changelog/changelog.sh
```

Write to a custom path:

```bash
bash skills/generate-changelog/changelog.sh -o /tmp/CHANGELOG.md
```

The script finds the latest git tag with `git describe --tags --abbrev=0` and
summarizes non-merge commits from that tag to `HEAD`. If no tag exists, it uses
all commits on the current branch.

## Categorization

- `Added`: commits starting with `feat`, `add`, `added`, or `new`
- `Fixed`: commits starting with `fix`, `fixed`, `bug`, `bugfix`, or `hotfix`
- `Removed`: commits starting with `remove`, `removed`, `delete`, `drop`, or
  `deprecate`
- `Changed`: all other non-merge commits, including docs, tests, chores,
  refactors, CI, and build changes

## Verification

This submission was tested on the real GitHub repository
`claude-builders-bounty/claude-builders-bounty`:

```bash
bash -n skills/generate-changelog/changelog.sh
bash skills/generate-changelog/changelog.sh -o skills/generate-changelog/samples/claude-builders-bounty.md
```
