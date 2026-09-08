# Changelog

## [Unreleased]

### Added

- Add 'shtab' project to contribution list (`cc1e188`)
- Add FAQ entry about \`edit()\` returning immediately (`ce57b87`)
- Add FAQ entry about tab completion in prompts (`cb43e05`)
- Add \`Option.get\_help\_spec\` to return the option's help left part (`271effb`)

### Fixed

- Fix \`copy\`, \`deepcopy\` and \`pickle\` of \`Sentinel\` members (`f58ca3e`)
- Fix race condition on \`KeyboardInterrupt\` arriving in \`Command.main()\` (`fc518e4`)

### Changed

- Deprecate \`isolated\_filesystem\` and document its limits (`fbdd434`)
- Revert "Deprecate \`isolated\_filesystem\` and document its limits" (`8ee83dd`)
- Start 8.5.1. (`dda8db4`)
- Document completion of path in shells (`c4597ed`)
- Test frozen types; Documents type conversion (`394088a`)
- Document calling a command as a regular function (`bb86cde`)
- Use the \`kbd\` role for keyboard sequences in the docs (`fa99fbd`)
- Split out types tests. (`b8a4486`)

### Removed

- Remove unused bindings and constants from \`\_winconsole\` (`94f17e2`)
