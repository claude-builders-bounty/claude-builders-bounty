# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-10-16

### Added

- Add `Parameter.spec` and deprecate `human_readable_name` ([`9f0bcdf`](https://github.com/pallets/click/commit/9f0bcdf0d868edfc71435cd0aac2dcc08cf94828))
- Add `Option.get_help_spec` to return the option's help left part ([`271effb`](https://github.com/pallets/click/commit/271effb3d96da5575eb527216ce3552bd7628fab))
- Add FAQ entry about tab completion in prompts ([`cb43e05`](https://github.com/pallets/click/commit/cb43e055741b2416bf3ec46b5f84b140cca23e18))
- Add FAQ entry about `edit()` returning immediately ([`ce57b87`](https://github.com/pallets/click/commit/ce57b87ac490ac8744491658d092bd86f571bf58))
- Add 'shtab' project to contribution list ([`cc1e188`](https://github.com/pallets/click/commit/cc1e188bf5ac6267c2a2a81e7b2c8ad7e55d2862))

### Fixed

- Fix short help abbreviation ([`f67c2bb`](https://github.com/pallets/click/commit/f67c2bb6c2f055c1c7a57cd46c3697fc26a7742e))
- Fix race condition on `KeyboardInterrupt` arriving in `Command.main()` ([`fc518e4`](https://github.com/pallets/click/commit/fc518e41218b447e875fe27244ae692c269bcb77))
- Fix `copy`, `deepcopy` and `pickle` of `Sentinel` members ([`f58ca3e`](https://github.com/pallets/click/commit/f58ca3e81424a35626c8a475eb59ab95589008ce))

### Changed

- Start 8.6.0. ([`a59f7c6`](https://github.com/pallets/click/commit/a59f7c624fb7272e37d97921047dab8bf3ff0675))
- Revert "Deprecate a parameter name that is not a Python identifier" ([`d036881`](https://github.com/pallets/click/commit/d036881798e34289a49b18a5c550c7cf687e5a7a))
- Always return a help record for an `Argument` ([`05f6fd0`](https://github.com/pallets/click/commit/05f6fd0df4ecbd104eb7a229f9f185c2484dee69))
- Move common `help` argument from `Option` and `Argument` to `Parameter` ([`405a548`](https://github.com/pallets/click/commit/405a5481e4dbd5022799993d787bd8446137d9a3))
- List every argument in the `Positional arguments` help section ([`f25f697`](https://github.com/pallets/click/commit/f25f697a439acc2b0d84aa8f5413330f4e2e75cf))
- `path_type` narrows the converted value's type for `convert` and `prompt` ([`22177f8`](https://github.com/pallets/click/commit/22177f857a34e3c35ba957553853a37f23feb37e))
- Split out types tests. ([`b8a4486`](https://github.com/pallets/click/commit/b8a4486d52083981babc1642449420db6b09662e))
- Use the `kbd` role for keyboard sequences in the docs ([`fa99fbd`](https://github.com/pallets/click/commit/fa99fbd7b96883c60275203b62914d3ce6d51010))
- Document calling a command as a regular function ([`bb86cde`](https://github.com/pallets/click/commit/bb86cdea6e83bc8e2711290eeffb4c8654baa7a3))
- Test frozen types; Documents type conversion ([`394088a`](https://github.com/pallets/click/commit/394088a09a210c152a4295e4a493ffdebd4c5047))
- Document completion of path in shells ([`c4597ed`](https://github.com/pallets/click/commit/c4597ed340477f3a69cfb8a9944149fab9d09b74))
- Start 8.5.1. ([`dda8db4`](https://github.com/pallets/click/commit/dda8db496c69db15d5146d68360f140c2515d6d0))
- Revert "Deprecate `isolated_filesystem` and document its limits" ([`8ee83dd`](https://github.com/pallets/click/commit/8ee83ddbf5a7a4c2eac5308c9599c5ee67ee005e))

### Removed

- Deprecate a parameter name that Click 9.0 will refuse or lower case ([`b90faad`](https://github.com/pallets/click/commit/b90faad1788bc030bb3320938f07c9189f42d7d0))
- Deprecate a parameter name that is not a Python identifier ([`e2bddbc`](https://github.com/pallets/click/commit/e2bddbc801dabc4efc3c3c1e32b53b3f938d3efc))
- Remove unused bindings and constants from `_winconsole` ([`94f17e2`](https://github.com/pallets/click/commit/94f17e276fbdd7348b88b05170923ecacb7b32bf))
- Deprecate `isolated_filesystem` and document its limits ([`fbdd434`](https://github.com/pallets/click/commit/fbdd434028fe07ecf35084c945b43b938dfd639f))

