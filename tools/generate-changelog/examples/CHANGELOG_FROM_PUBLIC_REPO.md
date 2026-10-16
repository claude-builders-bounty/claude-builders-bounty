<!-- Evidence: GitHub public repository https://github.com/pallets/click.git ; inspected tag 8.5.0 ; commits since tag 49 ; generated UTC 2026-10-16T00:54:07Z. -->

# Changelog

## [Unreleased] - 2026-10-16

Generated from commits since tag `8.5.0`.

### Added

- Add `Parameter.spec` and deprecate `human_readable_name`
- Add `Option.get_help_spec` to return the option's help left part
- Add FAQ entry about tab completion in prompts
- Add FAQ entry about `edit()` returning immediately
- Add 'shtab' project to contribution list

### Fixed

- Fix short help abbreviation
- Fix race condition on `KeyboardInterrupt` arriving in `Command.main()`
- Fix `copy`, `deepcopy` and `pickle` of `Sentinel` members

### Changed

- Deprecate a parameter name that Click 9.0 will refuse or lower case
- Start 8.6.0.
- Revert "Deprecate a parameter name that is not a Python identifier"
- Deprecate a parameter name that is not a Python identifier
- Always return a help record for an `Argument`
- Move common `help` argument from `Option` and `Argument` to `Parameter`
- List every argument in the `Positional arguments` help section
- `path_type` narrows the converted value's type for `convert` and `prompt`
- Split out types tests.
- Use the `kbd` role for keyboard sequences in the docs
- Document calling a command as a regular function
- Test frozen types; Documents type conversion
- Document completion of path in shells
- Start 8.5.1.
- Revert "Deprecate `isolated_filesystem` and document its limits"
- Deprecate `isolated_filesystem` and document its limits

### Removed

- Remove unused bindings and constants from `_winconsole`
