# Sample Output

**Command run on `tscircuit/schematic-trace-solver` (repo with tags):**

```bash
bash changelog.sh --dry-run
```

---

```markdown
# Changelog

All notable changes to this project will be documented in this file.
This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

---

## v0.0.48 — 2026-03-29

> Changes since `v0.0.47`. 2 commit(s) total.

### Fixed

- fix: exclude net-label-only nets from MSP pair queue (issue #79) ([9f3bee5](https://github.com/tscircuit/schematic-trace-solver/commit/9f3bee5...))

### Changed

- v0.0.47 ([e71dc7f](https://github.com/tscircuit/schematic-trace-solver/commit/e71dc7f...))
```

---

**Command run on a repo with no tags:**

```bash
bash changelog.sh --dry-run
```

```markdown
# Changelog

All notable changes to this project will be documented in this file.
This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

---

## [Unreleased] — 2026-03-29

> Changes all commits. 2 commit(s) total.

### Added

- feat: initial README with bounty board ([1aeae2a](https://github.com/owner/repo/commit/1aeae2a...))

### Changed

- Initial commit ([a80a580](https://github.com/owner/repo/commit/a80a580...))
```
