# Generate a changelog from Git history

A dependency-free Python tool with a Bash entry point for issue [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1). It reads commits after the nearest reachable tag and writes four sections: **Added**, **Fixed**, **Changed**, and **Removed**.

## Setup in three steps

1. Install Git and Python 3.10 or newer. Bash is optional on Windows; Git Bash works.
2. Copy this directory somewhere convenient, or use it directly from this repository.
3. Run `bash changelog.sh --repo /path/to/project` from this directory. On Windows PowerShell, use `python changelog.py --repo C:\path\to\project`.

The result is `CHANGELOG.md` in the target repository root. No packages, API keys, or model calls are needed. The Bash launcher checks that Python actually runs, so a nonfunctional Windows App Execution Alias does not hide a usable `python` installation.

## Preview and options

```bash
# Preview without writing to the repository
bash changelog.sh --repo /path/to/project --stdout

# Save a separate review copy, especially when a manual changelog already exists
bash changelog.sh --repo /path/to/project --output draft-changelog.md

# Select an explicit ancestor revision instead of the nearest tag
bash changelog.sh --repo /path/to/project --since v1.2.0 --stdout

# Check whether the generated section is current, without changing anything
bash changelog.sh --repo /path/to/project --check
```

An explicit `--output` is relative to the current working directory. The default is always the target repository root, even when invoked from elsewhere. Quote paths containing spaces.

Exit codes: `0` success/current, `1` stale or missing output in check mode, `2` invalid input or an operational error.

## Release range and classification

The default boundary is Git's `describe --tags --abbrev=0 HEAD`: the nearest **reachable** tag, including lightweight and annotated tags. It is not the lexically largest version and is not restricted to semantic versions. Use `--since` when a project also uses maintenance-line tags. An explicit boundary must be an ancestor of HEAD.

The tag commit is excluded. No reachable tag means all available history; a tag at HEAD produces four empty sections. Merged branch commits and merge commits are retained, each once, in reverse topological order. Shallow clones are rejected to prevent silently omitting releases. Fetch full history and tags explicitly before running; the tool itself never contacts a remote.

| Category | Recognized subjects |
| --- | --- |
| Added | `feat:`, `feature:`, `add:`, or plain Add/Introduce subjects |
| Fixed | `fix:`, `bugfix:`, `hotfix:`, or plain Fix/Repair/Resolve subjects |
| Removed | `remove:`, `delete:`, `drop:`, plain Remove/Delete/Drop subjects, or `chore:`/`refactor:` followed by those removal verbs |
| Changed | Other subjects, including documentation, builds, merges, and reverts |

Conventional Commit scopes and `!` breaking-change notation are supported. Original subjects are retained as escaped text, alongside commit identifiers. Classification is a deterministic heuristic, not a promise that every human commit message accurately describes its code. Review before publishing a release.

## Preserving release notes

The generated section is enclosed in unique `generate-changelog:start` and `generate-changelog:end` HTML comments. Later runs replace only that section. Manual content outside the markers and its newline style are preserved. Repeating the command with identical inputs does not rewrite the file.

An existing file without exactly one valid marker pair is refused. Preview with `--stdout` or choose a new output path; there is intentionally no force-overwrite option. Symlink destinations are refused. Git subprocesses receive argument arrays, and commit subjects are never executed as commands. Recognized GitHub remotes produce commit links without remote credentials.

## Tests and real-project example

```bash
python -m unittest discover -s . -p test_changelog.py -v
```

The suite creates isolated temporary Git repositories and covers tag boundaries, branch merges, missing tags, shallow histories, preservation of manual notes, stable output, unsafe-looking subjects, Unicode, custom output paths, and removal of credentials from links.

[SAMPLE_CHANGELOG.md](SAMPLE_CHANGELOG.md) was generated from the public [pallets/itsdangerous](https://github.com/pallets/itsdangerous) repository. See [SAMPLE_SOURCE.md](SAMPLE_SOURCE.md) for pinned commits and reproduction instructions. This is an actual Git-history run, not a hand-written demonstration.

## Limits

- Requires a non-bare Git working tree with at least one commit and complete local history.
- UTF-8 output; subjects with invalid source encoding are decoded with replacement characters.
- No network fetch, release publishing, changelog summarization service, or automatic version bump.
- The local Windows/Python and Git Bash checks do not establish a macOS/Linux CI run.
