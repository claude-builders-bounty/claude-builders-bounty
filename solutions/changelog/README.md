# Structured changelog generator

Solution for issue #1. Requires Git and Python 3; no packages, credentials or paid APIs.

## Setup (three steps)

1. Copy this directory to your machine.
2. Open a terminal in the full Git checkout you want to document (fetch full history and tags if needed).
3. Run `bash /path/to/changelog/changelog.sh` to create `CHANGELOG.md` in the current directory.

Alternatively: `bash changelog.sh --repo /path/to/repository --output /path/to/NEW_CHANGELOG.md`.
An existing output is never overwritten. Choose a new filename to regenerate.

## Release boundary and classification

The boundary is the nearest tag reachable along HEAD's **first-parent** history, as selected by `git describe --tags --abbrev=0 --first-parent`. This avoids treating a tag on a merged topic branch as the current branch's release. Lightweight and annotated tags are supported. All commits reachable after that boundary are included, including merged branches and merge commits. With no tag, all history is included. Empty history and shallow clones fail explicitly; no network fetch is performed.

Conventional `feat`/`add` commits map to Added; `fix`/`bugfix` to Fixed; `remove` to Removed. Leading add/introduce, fix/repair, and remove/delete/drop verbs also classify plain subjects. Remaining commits map to Changed. This is deterministic subject-based classification, not semantic AI inference. Subjects are Markdown-escaped and commit hashes included. A tagged HEAD produces four empty sections. Output has no generation timestamp and is reproducible at a fixed HEAD.

## Verification

Run `python3 -m unittest -v` in this directory. Six local Git-repository tests cover release boundaries, all four categories, merged topic tags, untagged history, Markdown escaping, tagged HEAD, existing-output preservation and shallow history rejection.

`SAMPLE_CHANGELOG.md` was generated against the real public repository https://github.com/claude-builders-bounty/claude-builders-bounty at commit `1aeae2adc82d33f971fd7731644348dcdd24b5a6`. This repository has no release tags and two commits, so the sample exercises the all-history fallback. The release-tag path is exercised by the regression tests. Reproduce by checking out that exact commit in a full clone and running the command with a fresh output path. The sample records both original commits exactly once.

AI assistance was used to implement, test and document this submission. A PR or passing tests do not establish acceptance or bounty payment.
