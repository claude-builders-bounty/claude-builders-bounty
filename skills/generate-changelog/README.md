# Generate Changelog

Dependency-free Bash tooling for generating a structured `CHANGELOG.md` from git history.

## Setup In 3 Steps

1. Copy `changelog.sh` into the root of any git repository.
2. Optional: copy `.claude/commands/generate-changelog.md` to enable `/generate-changelog` in Claude Code.
3. Run `bash changelog.sh` from the repository root.

## Usage

```bash
bash changelog.sh
```

Custom output path and repository path:

```bash
bash changelog.sh docs/CHANGELOG.md /path/to/repo
```

The generator detects the latest git tag with `git describe --tags --abbrev=0` and uses `tag..HEAD`. If no tags exist, it generates from the full history.

## Test

```bash
bash test_changelog.sh
```

The test creates a temporary tagged git repository and verifies that only commits after the tag appear in the generated changelog.
