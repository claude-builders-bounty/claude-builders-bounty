# Generate Changelog

Standalone Claude Code skill and Bash command for generating a structured
`CHANGELOG.md` from git history since the latest tag.

## Setup

1. Copy `changelog.sh` and `generate-changelog/` into any git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
```

If you prefer to run the implementation directly:

```bash
bash generate-changelog/changelog.sh
```

Optional flags:

```bash
bash generate-changelog/changelog.sh --repo . --output CHANGELOG.md --title "Project Changelog"
```

The command finds the latest git tag and reads commits from that tag to `HEAD`.
If the repository has no tags, it uses the full git history. Merge commits are
excluded so release notes stay focused on authored changes.

If your clone may not have the latest remote tags, run `git fetch --tags` before
generating the changelog.

## Categories

- `Added`: `feat`, `feature`, `add`, `create`, `implement`, `introduce`
- `Fixed`: `fix`, `bugfix`, `bug`, `repair`, `resolve`
- `Changed`: `docs`, `chore`, `refactor`, `perf`, `build`, `ci`, `test`, `style`,
  `update`, `change`, `improve`
- `Removed`: `remove`, `delete`, `drop`, `deprecate`, `revert`

Every rule has a reason: release readers care first about new capabilities,
corrections, behavior changes, and removals. Conventional Commits are supported,
but plain English commit subjects are also categorized.

## Tested

Tested on the real GitHub repository
`claude-builders-bounty/claude-builders-bounty` at commit `1aeae2a`.

Command:

```bash
bash generate-changelog/changelog.sh --output SAMPLE_CHANGELOG.md
```

Sample output is included in `SAMPLE_CHANGELOG.md`.

Also tested on the tagged real GitHub repository
`githubtraining/hellogitworld` using commits since `RELEASE_1.1`.

Command:

```bash
bash generate-changelog/changelog.sh --repo "$TEMP/repo-githubtraining-hellogitworld" --output CHANGELOG.codex.md
```

Sample output is included in `SAMPLE_TAGGED_REPO_CHANGELOG.md`.
