# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history since the latest tag.

## Setup In 3 Steps

1. Run from a git repository root:
   `bash skills/generate-changelog/changelog.sh`
2. Review the generated `CHANGELOG.md`.
3. Commit the changelog with your release or PR.

## Options

```bash
bash skills/generate-changelog/changelog.sh
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md
bash skills/generate-changelog/changelog.sh --since v1.2.0
```

## Categorization

- `Added`: `feat`, `add`, `new`, `introduce`
- `Fixed`: `fix`, `bug`, `security`, `patch`, `hotfix`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`
- `Changed`: everything else, including docs, refactor, chore, build, test,
  style, ci, and perf commits

See `sample-output.md` for output generated from a real GitHub repository.

## Validation

- Real GitHub repository: ran against `claude-builders-bounty/claude-builders-bounty`.
  The repository had no tags, so the script generated from full history.
- Tagged repository path: ran against a local validation repository with
  `v1.0.0` and four post-tag commits. The script generated exactly the
  `v1.0.0..HEAD` commits and placed one entry in each required category.
