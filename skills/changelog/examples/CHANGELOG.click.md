# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- generated-changelog:start -->

### Added
- Add 'shtab' project to contribution list (`cc1e188bf5ac`)
- Add FAQ entry about \`edit()\` returning immediately (`ce57b87ac490`)
- Add FAQ entry about tab completion in prompts (`cb43e055741b`)
- Add \`Option.get\_help\_spec\` to return the option's help left part (`271effb3d96d`)
- Add \`Parameter.spec\` and deprecate \`human\_readable\_name\` (`9f0bcdf0d868`)

### Fixed
- Fix \`copy\`, \`deepcopy\` and \`pickle\` of \`Sentinel\` members (`f58ca3e81424`)
- Fix race condition on \`KeyboardInterrupt\` arriving in \`Command.main()\` (`fc518e41218b`)
- Fix short help abbreviation (`f67c2bb6c2f0`)

### Changed
- Deprecate \`isolated\_filesystem\` and document its limits (`fbdd434028fe`)
- Revert "Deprecate \`isolated\_filesystem\` and document its limits" (`8ee83ddbf5a7`)
- Update Start 8.5.1. (`dda8db496c69`)
- Document completion of path in shells (`c4597ed34047`)
- Update Test frozen types; Documents type conversion (`394088a09a21`)
- Document calling a command as a regular function (`bb86cdea6e83`)
- Update Use the \`kbd\` role for keyboard sequences in the docs (`fa99fbd7b968`)
- Update Split out types tests. (`b8a4486d5208`)
- Update \`path\_type\` narrows the converted value's type for \`convert\` and \`prompt\` (`22177f857a34`)
- Update List every argument in the \`Positional arguments\` help section (`f25f697a439a`)
- Update Move common \`help\` argument from \`Option\` and \`Argument\` to \`Parameter\` (`405a5481e4db`)
- Update Always return a help record for an \`Argument\` (`05f6fd0df4ec`)
- Deprecate a parameter name that is not a Python identifier (`e2bddbc801da`)
- Revert "Deprecate a parameter name that is not a Python identifier" (`d036881798e3`)
- Update Start 8.6.0. (`a59f7c624fb7`)
- Deprecate a parameter name that Click 9.0 will refuse or lower case (`b90faad1788b`)

### Removed
- Remove unused bindings and constants from \`\_winconsole\` (`94f17e276fbd`)

<!-- generated-changelog:end -->

