# Issue #1 — Structured CHANGELOG generator

## Setup (3 steps)
1. Copy `issue-1/changelog.sh` into your repo root.
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh`

The script reads commits since the last git tag, auto-categorizes entries into **Added / Fixed / Changed / Removed**, and writes `CHANGELOG.md`.

Sample output: `issue-1/examples/sample-output.md`.
