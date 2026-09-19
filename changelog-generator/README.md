# Git changelog generator

Run `bash changelog.sh` from any Git repository to generate a structured
`CHANGELOG.md` from commits since the latest tag. Commit subjects are grouped
into `Added`, `Fixed`, `Changed`, and `Removed`; commits without a matching
keyword go into `Changed`.

## Setup and use

1. Copy `changelog.sh` into the project root.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

Use `bash changelog.sh --output docs/CHANGELOG.md` to select another output
path. The script uses only standard Bash and Git.
