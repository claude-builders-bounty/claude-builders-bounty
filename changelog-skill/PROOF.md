# PROOF — changelog skill test evidence

- `bash tests/test_changelog.sh` → **10 green / 0 red** (macOS bash 3.2):
  exit-0, 4 groups, feat→Added, fix→Fixed, short-SHA, Keep-a-Changelog header,
  preview-no-write, unknown-tag fail-closed, empty-range fail-closed, --version.
- Sample `samples/CHANGELOG.homelab-sample.md`: 6 real commits from
  `illbnm/homelab-stack` → B:0 A:1 F:1 C:4 R:0, every bullet with short-SHA.
