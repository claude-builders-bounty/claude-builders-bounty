# Generate a structured CHANGELOG

## Description
Create a categorized `CHANGELOG.md` from git history, grouped into **Added**, **Fixed**, **Changed**, and **Removed**.

## Command
- `/generate-changelog`

## Steps
1. Run `/generate-changelog` (or `bash changelog.sh`) in the project root.
2. The skill gathers commits since the latest tag (or all commits if none exist) and writes a formatted `CHANGELOG.md`.
3. Review the generated changelog and commit it when ready.
