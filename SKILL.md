# Generate Changelog

Use `/generate-changelog` in a git repository to create a categorized `CHANGELOG.md`
from commits since the latest tag.

## Steps

1. Run `bash changelog.sh`
2. Review `CHANGELOG.md`
3. Commit the generated file if desired

## Notes

- Categories: `Added`, `Fixed`, `Changed`, `Removed`
- Uses the latest reachable tag from `git describe --tags --abbrev=0`
- Falls back to the full git history if the repo has no tags
