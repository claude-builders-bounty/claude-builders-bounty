# Changelog Generator

Generates a Keep-a-Changelog `CHANGELOG.md` from every non-merge commit after the latest reachable Git tag. Conventional commits map to the contract's literal `Added`, `Fixed`, `Changed`, and `Removed` sections; non-conventional commits are retained under `Changed`.

## Setup and use (2 steps)

1. Make the command executable: `chmod +x skills/changelog-generator/changelog.sh`
2. From any Git repository run: `/path/to/skills/changelog-generator/changelog.sh` (or pass the repository path as its only argument)

The command writes `CHANGELOG.md` in the target repository. Advanced use can call `scripts/generate_changelog.py` with `--since-tag`, `--version`, `--date`, and `--output`.

## Verification

Run `python3 -m pytest -q skills/changelog-generator/tests`. The regression suite creates real temporary Git repositories, tags and commits, then runs the same Bash entry point a user runs. `SAMPLE_OUTPUT.md` records output from a public real repository.
