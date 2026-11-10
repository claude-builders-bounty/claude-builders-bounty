# changelog.sh

Generate a structured `CHANGELOG.md` from git history: commits since the last tag,
sorted into **Added / Fixed / Changed / Removed** ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format).

Needs only `bash` and `git`. No other dependencies. It avoids bash-4-only features so it
should also run on macOS's stock bash 3.2 (tested on bash 5.3).

## Setup and usage (3 steps)

1. **Download** the script:
   ```bash
   curl -fsSLO https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog/changelog.sh
   ```
2. **Go to** the repository you want a changelog for: `cd path/to/your-repo`
3. **Run** it:
   ```bash
   bash /path/to/changelog.sh
   ```
   This writes `CHANGELOG.md`. Use `bash changelog.sh docs/CHANGES.md` for another path, or `bash changelog.sh -` to print to stdout.

## What it does

| Situation | Result |
|---|---|
| Commits after the latest tag | `## [Unreleased]` section with those commits |
| HEAD is exactly on a tag | `## [v1.2.0] - YYYY-MM-DD` with the commits since the previous tag |
| No tags at all | Every commit in history |
| No commits yet | `_No commits yet._` |
| `CHANGELOG.md` already exists | Your intro and older releases are kept; the old `[Unreleased]` (or same-version) section is replaced, so re-running never duplicates |

**Categorization**

| Commit | Section |
|---|---|
| `feat:` / `feat(scope):` | Added |
| `fix:` / `bugfix:` / `hotfix:` | Fixed |
| any type whose description starts with *remove, delete, drop, deprecate* | Removed |
| other Conventional Commit types (`docs`, `chore`, `refactor`, `perf`, `ci`, ...) | Changed, labelled with the type |
| plain messages starting with *Add/Create/Implement/Introduce* | Added |
| plain messages starting with *Fix/Resolve/Patch/Correct* | Fixed |
| plain messages starting with *Remove/Delete/Drop/Deprecate* | Removed |
| anything else | Changed |

`type!:` or a `BREAKING CHANGE:` footer adds a **BREAKING:** marker. Merge commits are skipped.
`<`, `>` and `&` are HTML-escaped so commit subjects can't break the Markdown; all other
characters are kept as written. When `origin` is a GitHub URL, hashes link to the commit
(any credentials in the remote URL are never written out).

## Tests

```bash
bash test.sh
```

Builds throwaway repos covering: no repo, empty history, no tags, tags, HEAD on a tag,
re-runs, existing changelog merge, merge commits, special characters/unicode, breaking
changes, stdout mode, and GitHub links.

Real-repo samples generated from [axios/axios](https://github.com/axios/axios) are in [`examples/`](examples/).
