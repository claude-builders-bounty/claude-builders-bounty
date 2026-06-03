# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-06-03

### Added

- add `msg-value-loop` (#15050)
- add `controlled-delegatecall` (#15046)
- add channel reserve precompile support (#15036)
- add `[profile.<name>.coverage]` config section (#14599)
- decode Tempo T5 surfaces (#15032)
- add TIP-20 logo URI tooling (#15034)
- mutation testing (#13091)
- wire T5 implicit approval behavior and cheatcodes (#15022)

### Changed

- update `solar` to latest main (#15003)
- add T5 local execution coverage (#15045)
- Use TUI fallback for debugger in non-interactive mode (#14780)
- config` semantics (CLI true wins; CLI false
- Fix mutation source path normalization on Windows (#15044)

### Fixed

- identify forked contracts in debug traces (#15048)
- preserve nested if blocks with multiple statements (#14985)
- preserve debug traces when setUp reverts (#14390)
- avoid arbitrary-send-eth modifier blowups (#15041)
- avoid unnecessary reentrancy call classification (#15042)
- keep timed invariant workers running until timeout (#15043)
- qualify shadowed event module paths (#15008)
- make forge rerun filtering contract-aware (#14994)

