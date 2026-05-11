# Generate Changelog from Git History

Claude Code skill for generating a structured `CHANGELOG.md` from commits since the latest git tag.

## Command

`/generate-changelog`

## What this skill does

When the user asks to generate a changelog:

1. Verify the current directory is a git repository.
2. Run `bash changelog.sh` from the project root.
3. Review the generated `CHANGELOG.md` for obvious formatting issues before reporting success.

## Categorization rules

Use the included `changelog.sh` script. It groups commits into the required sections:

- `Added`: `feat:`, `feature:`, `add`, `adds`, `new`
- `Fixed`: `fix:`, `bugfix:`, `bug`, `regression`
- `Changed`: docs, refactors, chores, CI/build/test/style/performance updates, and uncategorized commits
- `Removed`: `remove:`, `delete:`, `drop`, `removed`, `deleted`
- `Breaking Changes`: highlighted when a commit contains `!:` or `BREAKING CHANGE`

## Usage

```bash
bash changelog.sh
```

Optional:

```bash
bash changelog.sh --dry-run
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --since-tag v1.2.3
```

## Success criteria

A successful run:

- detects the latest git tag automatically
- reads commits since that tag
- writes a formatted `CHANGELOG.md`
- preserves older release sections when updating an existing changelog
- requires no external dependencies beyond bash and git
