# Generate Changelog Skill

This implements bounty #1 with a Claude Code skill and a `bash changelog.sh` command.

## Setup

1. Copy `changelog.sh` and `skills/generate-changelog/` into a git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh --repo /path/to/project
bash changelog.sh --repo /path/to/project --output docs/CHANGELOG.md
bash changelog.sh --repo /path/to/project --dry-run
```

The script finds the latest git tag and collects commits after it. If no tag exists, it uses the full git history. Commit subjects are categorized into `Added`, `Fixed`, `Changed`, or `Removed` using conventional commit types and common release verbs.

## Verification

```bash
python -m unittest discover -s tests
bash changelog.sh --dry-run
```

Sample output from this real GitHub repository is included at `samples/claude-builders-bounty-changelog.md`.
