# Real repository sample

Repository: https://github.com/pallets/click

Generated from `8.5.0..HEAD` using `bash bounty-1/changelog.sh --stdout`.

## Unreleased - 2026-09-21

### Added
- Add `Option.get_help_spec` to return the option's help left part (`271effb`)
- Add FAQ entry about tab completion in prompts (`cb43e05`)
- Add FAQ entry about `edit()` returning immediately (`ce57b87`)
- Add 'shtab' project to contribution list (`cc1e188`)

### Fixed
- Fix short help abbreviation (`f67c2bb`)
- Fix race condition on `KeyboardInterrupt` arriving in `Command.main()` (`fc518e4`)
- Fix `copy`, `deepcopy` and `pickle` of `Sentinel` members (`f58ca3e`)

### Changed
- Revert "Deprecate a parameter name that is not a Python identifier" (`d036881`)
- Deprecate a parameter name that is not a Python identifier (`e2bddbc`)
- Always return a help record for an `Argument` (`05f6fd0`)
- Move common `help` argument from `Option` and `Argument` to `Parameter` (`405a548`)
- List every argument in the `Positional arguments` help section (`f25f697`)
- `path_type` narrows the converted value's type for `convert` and `prompt` (`22177f8`)
- Split out types tests. (`b8a4486`)
- Use the `kbd` role for keyboard sequences in the docs (`fa99fbd`)
- Document calling a command as a regular function (`bb86cde`)
- Test frozen types; Documents type conversion (`394088a`)
- Document completion of path in shells (`c4597ed`)
- Start 8.5.1. (`dda8db4`)
- Revert "Deprecate `isolated_filesystem` and document its limits" (`8ee83dd`)
- Deprecate `isolated_filesystem` and document its limits (`fbdd434`)

### Removed
- Remove unused bindings and constants from `_winconsole` (`94f17e2`)
