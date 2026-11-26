<!--
Sample output — generated from a real GitHub repository.

Repo:     https://github.com/pallets/markupsafe
Command:  python3 generate_changelog.py --repo /tmp/markupsafe --dry-run
Run:      2026-11-11 (UTC) — tool version 1.0.0
Range:    3.0.4..HEAD (latest tag 3.0.4, 22 commits)
Result:   12 entries — 10 merge commits skipped, 0 duplicates removed.
          Added 0, Fixed 0, Changed 5, Removed 7.

Note the honest edge cases this sample shows:
- "Release version 3.0.4" and "Start version 3.1.0" land in Changed
  (no add/fix/remove signal — nothing is silently dropped);
- the Revert commit is kept as "Revert: Delete CONTRIBUTING.rst";
- near-duplicate subjects ("drop python 3.10 (#538)" vs
  "drop python 3.10") are kept as separate entries because their
  text differs — de-duplication is exact-match only.
-->

# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-11-11

### Changed

- Update dependencies
- Release version 3.0.4 (#537)
- Update uv.lock
- Revert: Delete CONTRIBUTING.rst
- Start version 3.1.0

### Removed

- Drop python 3.10 (#538)
- Drop python 3.10
- Remove previously deprecated code (#499)
- Remove previously deprecated code
- Drop end of life python versions (#498)
- Drop end of life python versions
- Delete CONTRIBUTING.rst
