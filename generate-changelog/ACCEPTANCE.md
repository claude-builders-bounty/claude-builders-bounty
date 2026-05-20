# Acceptance Checklist

This checklist maps the bounty requirements to the files and commands in this PR.

- Works via `/generate-changelog` command or `bash changelog.sh`
  - `/generate-changelog`: `.claude/commands/generate-changelog.md`
  - Claude Code skill: `.claude/skills/generate-changelog/SKILL.md`
  - Bash command: `bash changelog.sh`

- Fetches commits since the last git tag
  - Implemented in `changelog.sh` with `git describe --tags --abbrev=0` and the `${latest_tag}..HEAD` range.
  - Covered by `bash generate-changelog/test-changelog.sh ./changelog.sh`, which creates a temporary `v1.0.0` tag and verifies pre-tag commits are excluded.

- Auto-categorizes into `Added`, `Fixed`, `Changed`, and `Removed`
  - Implemented in `changelog.sh` with conventional-commit-style prefixes and keyword fallbacks.
  - Covered by the smoke test using `feat:`, `fix:`, `docs:`, and `remove:` commits.

- Outputs a properly formatted `CHANGELOG.md`
  - `changelog.sh` writes a Markdown document with a `# Changelog` heading and all four sections.

- Tested on a real GitHub repo with sample output
  - Sample output is included in `generate-changelog/SAMPLE_OUTPUT.md`.
  - The same output is shown in `generate-changelog/README.md`.

- README with setup instructions in 3 steps or fewer
  - `generate-changelog/README.md` has a three-step setup section.

## Verification Commands

```bash
bash -n changelog.sh
bash generate-changelog/test-changelog.sh ./changelog.sh
```

The branch also includes `.github/workflows/generate-changelog.yml`, which runs the same syntax and smoke-test checks on push and pull request events.
