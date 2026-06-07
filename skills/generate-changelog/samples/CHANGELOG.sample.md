# Changelog

## [Unreleased] - 2026-06-07

### Added

- add --append mode and breaking-change detection for changelog (a163122)
- add repo-root changelog.sh entrypoint for bounty #1 (94408fe)
- add --version flag to changelog generator (18ef0b4)
- add --preview flag to changelog generator (0e7e802)
- add generate-changelog skill (bounty #1) (a353ed8)
- initial README with bounty board (1aeae2a)

### Fixed

- strip colon after conventional commit prefix in changelog bullets (9f749e0)
- strip docs/chore/ci prefixes in changelog bullets (fef62ca)
- improve commit prefix parsing and upstream CI visibility (1aa639a)

### Changed

- sync PROOF.md with 24 tests and root changelog.sh (d015773)
- add PROOF.md and CI guard for changelog bounty (56102e5)
- document --version flag in generate-changelog SKILL.md (a115b01)
- run changelog tests on feature branch pushes (e5b313e)
- trigger changelog tests when workflow file changes (a3b19e2)
- use clean upstream-main output for changelog sample (bf6cc95)
- add changelog test workflow and refresh sample output (a7ec703)
- refresh sample output and add --since test (8b7f8d2)
- Initial commit (a80a580)

