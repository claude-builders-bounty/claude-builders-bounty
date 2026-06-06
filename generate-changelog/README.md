# Generate Changelog Skill

Create a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh` and the `generate-changelog/` folder into the target repository.
2. Run `bash changelog.sh --output CHANGELOG.md` or preview a public repo with `bash changelog.sh --repo owner/name --dry-run`.
3. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections before committing.

See `samples/CHANGELOG.sample.md` for an output generated from a real GitHub repository.
