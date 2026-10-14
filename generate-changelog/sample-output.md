# Sample Output — Real-Repo Test

- **Repo:** https://github.com/chalk/chalk (cloned locally, full history + tags)
- **Tag range:** `v5.6.2..v6.0.1` (12 commits)
- **Command:** `bash changelog.sh --repo <chalk-clone> --from v5.6.2 --to v6.0.1 --version 6.0.1`
- **Result:** 12 commits categorized (Added=1, Fixed=4, Changed=7, Removed=0), 0 dropped; merge commits: none in range
- **Notes:** PR refs (#689, #688, #687, #670, #664) preserved; `Fix:` prefix stripped; bare release commits (`6.0.1`, `6.0.0`) land in Changed per the documented mapping.

---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [6.0.1] - 2026-10-08

### Added

- Add extended underline styles and underline colors (#689)

### Fixed

- Fix inconsistent coercion of two arguments
- Treat a numeric `FORCE_COLOR` as an exact level (#688)
- Downsample `ansi256()` and `bgAnsi256()` to 16 colors at level 1 (#687)
- Fix typos (#664)

### Changed

- 6.0.1
- Meta tweaks
- 6.0.0
- Improve performance
- Require Node.js 22
- Optimize 2-argument calls (#670)
- Tweaks

