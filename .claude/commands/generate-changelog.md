# Generate Changelog

Run this command from the repository root:

    bash changelog.sh

The script finds the latest Git tag with git describe --tags --abbrev=0 and writes CHANGELOG.md from commits since that tag. If the repository has no tags, it documents all commits reachable from HEAD.
