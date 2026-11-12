# changelog.sh

Generate a structured `CHANGELOG.md` from git history. Categorises commits into **Added / Changed / Fixed / Removed**. No dependencies beyond `git` and bash.

## Setup in 3 steps

1. Copy `changelog.sh` into your repo (or keep it anywhere and call it by path).
2. Make it executable: `chmod +x changelog.sh`.
3. Run it: `bash changelog.sh` — it reads commits since the last git tag (or the first commit if there are no tags) and writes `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh                          # since last tag, heading "[Unreleased]"
bash changelog.sh --from v1.2.0            # since a specific ref
bash changelog.sh --version 1.3.0          # heading "[1.3.0] - <today>"
bash changelog.sh --out docs/CHANGELOG.md  # write somewhere else
bash changelog.sh --include-merges         # merge commits are skipped by default
```

## How commits are categorised

| Commit prefix (case-insensitive) | Section |
| --- | --- |
| `feat`, `feature`, `add`, `new` | Added |
| `fix`, `bugfix`, `hotfix`, `patch` | Fixed |
| `remove`, `delete`, `drop`, `deprecat` | Removed |
| anything else (chore, docs, refactor, test, …) | Changed |

Scopes are stripped: `feat(cli): add --json` becomes `add --json`.

## Behaviour worth knowing

- **Idempotent.** Running it twice over the same range does not duplicate the entry — it prints `already up to date` and exits 0.
- **Never destroys history.** If `CHANGELOG.md` exists, the new section is prepended above the old content.
- **No tags?** It falls back to the root commit and includes everything.
- **Fails loudly.** Running outside a git repo, or with an unknown ref, exits non-zero with a message instead of writing a broken file.

## Tests

```bash
bash tests/run-tests.sh
```

Eleven checks: the four categories, the Unreleased heading, the no-tag fallback, `--version`, `--from`, idempotency, rejection of non-git directories, and prepending to an existing changelog.

## Claude Code skill

`SKILL.md` in this directory exposes the same behaviour as `/generate-changelog`. See the file for the interface contract.
