# Generate Changelog Skill

## Setup

1. Copy `generate-changelog/` into your Claude Code skills directory or keep it in your project.
2. From a git repository, run `bash generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

The script reads commits since the latest reachable git tag and writes categorized `Added`, `Fixed`, `Changed`, and `Removed` sections.

Sample output from the real GitHub repo `pallets/markupsafe` is included at `samples/markupsafe-sample-changelog.md`.
