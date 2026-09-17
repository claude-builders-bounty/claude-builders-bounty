# Changelog

<!-- generate-changelog:start -->
## [Unreleased]

Range: since tag 8\.5\.0; 15 non-merge commit(s).

### Added

- Add FAQ entry about \`edit\(\)\` returning immediately (`ce57b87ac490`)
- Add 'shtab' project to contribution list (`cc1e188bf5ac`)
- Add FAQ entry about tab completion in prompts (`cb43e055741b`)
- Add \`Option\.get\_help\_spec\` to return the option's help left part (`271effb3d96d`)

### Fixed

- Fix \`copy\`, \`deepcopy\` and \`pickle\` of \`Sentinel\` members (`f58ca3e81424`)
- Fix race condition on \`KeyboardInterrupt\` arriving in \`Command\.main\(\)\` (`fc518e41218b`)

### Changed

- Deprecate \`isolated\_filesystem\` and document its limits (`fbdd434028fe`)
- Revert "Deprecate \`isolated\_filesystem\` and document its limits" (`8ee83ddbf5a7`)
- Document completion of path in shells (`c4597ed34047`)
- Test frozen types; Documents type conversion (`394088a09a21`)
- Document calling a command as a regular function (`bb86cdea6e83`)
- Use the \`kbd\` role for keyboard sequences in the docs (`fa99fbd7b968`)
- Split out types tests\. (`b8a4486d5208`)
- Start 8\.5\.1\. (`dda8db496c69`)

### Removed

- Remove unused bindings and constants from \`\_winconsole\` (`94f17e276fbd`)

<!-- generate-changelog:end -->
