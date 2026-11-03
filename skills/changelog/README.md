# Git-history CHANGELOG generator

A dependency-free implementation of [bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1). The accepted Bash/Python route requires no Claude subscription, API key, model call, package installation, or hosted service.

## Setup and use — three steps

1. Have Git, Bash, and Python 3.10+ available, and copy this entire directory together. On Windows use Git Bash with `python3` available, or set `PYTHON` to your Python executable. No administrator rights or dependency downloads are performed by the generator.
2. From this directory, preview your repository: `bash changelog.sh --repo /path/to/repository --dry-run`.
3. Write and inspect the printed diff: `bash changelog.sh --repo /path/to/repository`. Review the resulting `CHANGELOG.md` before committing it.

## Behavior

- Default range is the nearest reachable tag reported by `git describe --tags --abbrev=0` through HEAD, excluding the tag commit. This is not a global maximum semantic version or the newest tag on an unrelated branch.
- A complete repository without tags uses all reachable history. A shallow clone without a reachable tag is refused rather than described as a complete history. The tool does not fetch or deepen repositories automatically.
- Override bounds with `--from REF --to REF`; both are resolved to commit IDs before inspection. The starting commit must be an ancestor of the ending commit.
- Merge commits are omitted to avoid repeating merged commit descriptions. This means merge-message-only changes are not summarized.
- Conventional `feat` maps to Added, `fix`/`bugfix` to Fixed, and removal types or descriptions to Removed. Other relevant changes map to Changed. Plain subjects starting with add/introduce, fix/repair/resolve, or remove/delete/drop use the corresponding categories. Empty categories are omitted.
- Routine chore, ci, style, and test commits are excluded unless their subject has `!` or their body has a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer. Breaking entries receive an inline bold marker while retaining the requested four-category format.
- Descriptions retain the commit's meaning, include a 12-character commit hash, and escape Markdown/HTML controls. This is deterministic rule-based classification, not a claim of human-quality semantic analysis. There is no invented release version/date, PR URL, capability, or security guarantee.
- Only a managed block under `## [Unreleased]` is regenerated. Manual notes outside that block and historical release entries are retained; generated content can be overwritten on the next run, so keep manual edits outside the markers. A malformed managed block is refused. Repeated execution is byte-identical for unchanged inputs.
- Git inspection does not run project code, install hooks, stage files, commit, push, tag, or contact a model. One explicitly selected output file is written atomically. Symlinks and Git metadata destinations, including linked-worktree common metadata and the `.git` pointer, are refused. This is not a sandbox for hostile Git binaries or an operating-system permission boundary.
- Output is UTF-8. Existing historical CRLF bytes are retained. Explicit `--output PATH` is relative to your current working directory, not `--repo`. For bare repositories, select an external output path.

## Options

```bash
bash changelog.sh --repo /path/to/project --from v1.0.0 --to HEAD --dry-run
bash changelog.sh --repo /path/to/project --output /path/to/review/CHANGELOG.md
python3 generate_changelog.py --help
```

`PYTHON=/path/to/python3 bash changelog.sh ...` selects a specific interpreter.

## Verification

```bash
python3 -m unittest discover -s tests -v
bash -n changelog.sh
```

The recorded run passed 22 black-box tests using clearly synthetic, isolated local Git histories: four-category output, tag/no-tag history, idempotency, preserved manual/historical text, CRLF, dry-run, invalid/reversed refs, breaking chores, hostile Markdown, unusual body delimiters, symlinks, Git metadata and worktree-pointer protection, incomplete shallow history, non-repositories, unborn HEAD, explicit bounds, and unchanged Git refs.

A separate actual run inspected public [`pallets/click`](https://github.com/pallets/click) history from tag `8.5.0` to commit `2247b35ea1c47c727d7a06e51fa280e12a863ff6`. It produced 25 entries from 25 non-merge commits. The source was a shallow bare clone with the selected tag available. Every emitted hash was checked against the selected range, a repeated run produced identical bytes, and the source refs/config remained unchanged. Its source code was never checked out or executed.

See `examples/CHANGELOG.click.md`, `examples/source-verification.json`, and `verification/test-run.txt`. These prove this recorded local execution, not maintainer acceptance, production integration, reserved bounty funding, or payment eligibility. This is an AI-assisted contribution. Automated checks and agent review do not constitute independent human review or a payment guarantee.
