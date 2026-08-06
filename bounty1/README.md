# Structured changelog generator

AI-assisted deliverable for the $50 bounty in [issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## Setup and use

1. Copy `changelog.sh` into a Git repository and make it executable: `chmod +x changelog.sh`.
2. Run `bash changelog.sh` (or add `--output docs/CHANGELOG.md --version 1.2.0`).
3. Review the generated `CHANGELOG.md` and commit it with the project’s normal workflow.

The default range is from the most recent reachable Git tag to `HEAD`. If the repository has no tag, the script uses its full history. Use `--since REF` to choose an explicit lower bound. GitHub commit links are added automatically when `origin` points to GitHub.

## Categories

Conventional prefixes and common verbs are mapped to `Added`, `Fixed`, or `Removed`. Other subjects go into `Changed`. The full commit subject is preserved after a conventional-commit prefix is removed.

## Local verification

`tests/test_changelog.sh` creates a temporary Git repository, tags a baseline, adds representative commits, runs the generator, and checks the four required sections plus commit text.

## AI disclosure

This package was created with AI assistance. A human should review the shell logic, generated changelog, portability, and licensing before submitting it to the bounty maintainer.
