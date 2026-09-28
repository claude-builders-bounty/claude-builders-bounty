# Structured CHANGELOG generator

Generates a categorized `CHANGELOG.md` from Git history.

## Requirements

Bash 4 or later (uses `mapfile`), Git, and a repository containing at least one commit. Run from the repository whose history you want to document. On macOS, use a separately installed Bash 4+ rather than the system Bash 3.2. The regression suite additionally requires Python 3.

## Setup

1. Make it executable: `chmod +x skills/generate-changelog/changelog.sh`
2. Run from a Git repository root: `bash skills/generate-changelog/changelog.sh`
3. Review the generated `CHANGELOG.md` before release.

The script reads commits since the latest reachable Git tag. If no tag exists, all available history is used. Merge commits are excluded. This writes an Unreleased snapshot, replacing the selected output file; it does not append older release sections. Supply another path to preserve your existing changelog, for example `bash skills/generate-changelog/changelog.sh 'release notes.md'`.

## Categories

- Added: `feat`, `add`, and `new` subjects.
- Fixed: `fix`, `bug`, and `hotfix` subjects.
- Removed: `remove`, `removed`, `delete`, and `drop` subjects.
- Changed: other subjects.

Scoped `feat`/`fix`/`remove`/`delete`/`drop` and breaking `feat!`/`fix!`/`remove!` forms are supported. Subjects are printed as text, never executed. Repository/HEAD/log errors return nonzero before opening the output, so those failures do not overwrite existing release notes or report success.

## Reproducible validation

```bash
bash -n skills/generate-changelog/changelog.sh
python3 skills/generate-changelog/test_changelog.py
```

The ten tests create temporary Git repositories and use real Git and Bash. They cover tag ranges, no tags, an empty post-tag range, categories, scoped/breaking subjects, paths containing spaces, literal shell-looking subjects, invalid/empty repositories, simulated Git-log failure, and an invalid output directory. Only the Git-log-failure case substitutes a small Git wrapper; other Git calls are real. No GitHub credentials or network calls are needed.

On 2026-09-28 this suite reproduced four failures in the previous script and passed all ten tests after the correction. `bash -n` also passed. These are isolated local regressions, not GitHub-hosted CI or maintainer acceptance. The previously submitted real-repository sample remains in `SAMPLE_CHANGELOG.md`; this regression run did not regenerate that sample.
