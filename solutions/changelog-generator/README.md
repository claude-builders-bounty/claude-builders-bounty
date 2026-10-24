# Git changelog generator

Generate `CHANGELOG.md` from commits since the most recent Git tag, categorized as **Added**, **Fixed**, **Changed**, and **Removed**. Uses only Bash and Git. When no tag exists, includes all commits.

## Setup and usage (2 steps)

1. Copy `changelog.sh` into a Git repository and run `chmod +x changelog.sh`.
2. Run `./changelog.sh` (or `./changelog.sh output.md`).

Commits starting with `feat:` or `feat(scope):` go to Added; `fix:` and `fix(scope):` to Fixed; `remove:`, `removed:`, `revert:`, `delete:`, or `drop:` to Removed. All others go to Changed. Merge commits are excluded. Output is overwritten on each run. This script reads commit subjects; it does not invoke AI.

See `SAMPLE-CHANGELOG.md` for output generated from a real GitHub repository clone. Run `bash test.sh` for isolated regression tests.
