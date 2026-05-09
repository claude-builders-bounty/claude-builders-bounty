## [Unreleased] - 2026-05-09

### Added
- Add NoSuchCommand exception with suggestions for misspelled commands (#3228) ([`831c8f0`](https://github.com/pallets/click/commit/831c8f0948af519e45b90801d7430ff25451f972))
- Add file-like pager: `click.get_pager_file()` (#1572) ([`c69643b`](https://github.com/pallets/click/commit/c69643b60cf971cd5d8e5d3902632807ceab9b8f))
- Add parametrized tests for `should_strip_ansi` ([`cf0c36d`](https://github.com/pallets/click/commit/cf0c36d33734af1de9ecd5d3305970eb26ebba7f))
- add codespell pre-commit hook ([`e3c0898`](https://github.com/pallets/click/commit/e3c0898975a7e095a3f11fd2d13035872a55a3e5))

### Changed
- `FuncParamType` should use `ValueError` message in `self.fail()` (#3211) ([`fc6c7c4`](https://github.com/pallets/click/commit/fc6c7c47edd6110b6bd5a1a5297b2035214b0cd1))
- Localisation of more strings (#2902) ([`5b9630f`](https://github.com/pallets/click/commit/5b9630f50fde938b72ad8c99542efe3a6f5717e2))
- Move #1572 changelog entry to correct version entry (8.4.0). ([`fed9049`](https://github.com/pallets/click/commit/fed9049f7a07550d560a91b30c5b0b3e17d54981))
- `Parameter` typing improvements (#2805) ([`ddede21`](https://github.com/pallets/click/commit/ddede2147c9370ab8275f81db4826b6895d2e7dc))
- Extract `_guess_type` from `convert_type` and add overloads (#3372) ([`d2e4a42`](https://github.com/pallets/click/commit/d2e4a42ff410d92e88293f3552422a4a284c749b))
- Move changes to correct section ([`a34f960`](https://github.com/pallets/click/commit/a34f960488e777ae795c41de7d33ae3c6edeb6fb))
- Put changes in correct section. ([`235e03e`](https://github.com/pallets/click/commit/235e03ee0cb8d575630427158393a9c6fce39b31))
- Put changes in correct section ([`94004f1`](https://github.com/pallets/click/commit/94004f1b5a4a982e8e33ef8d5f00cfb0e1dabddd))
- Split string values from `default_map` for multi-value parameters ([`3a3e035`](https://github.com/pallets/click/commit/3a3e0350b6a2ea3e799440d48e779acabcf44de9))
- Update examples in docs, adds version update admonitions ([`ded5b69`](https://github.com/pallets/click/commit/ded5b692472629154ab5a2f63bd7cdd4deea3146))
- Make `FuncParamType` is generic ([`78a4efc`](https://github.com/pallets/click/commit/78a4efcdce1067566fa58771afbaeb18e2c1cf0f))
- Eliminate one type ignore ([`3e2d92c`](https://github.com/pallets/click/commit/3e2d92c590c34c92e116acdda71e7678ca50895e))
- Narrow down type ignore ([`6e981ed`](https://github.com/pallets/click/commit/6e981edefaeafa6c16b478dc131fba4d936024f1))
- ParamType typing improvements ([`5989375`](https://github.com/pallets/click/commit/5989375dc3953a5709c411e11f658c242319858e))
- Use non-shadowed help option name in error hint ([`1241aba`](https://github.com/pallets/click/commit/1241abaed4e441582a21f4bf90c8482de02b92df))
- Auto-detect `type=UNPROCESSED` when `flag_value` has non-basic types ([`4e4c7a6`](https://github.com/pallets/click/commit/4e4c7a69b7953ccb8c14e92368ca65d9525f1d2b))
- Compile Click-specific guidelines ([`32ac271`](https://github.com/pallets/click/commit/32ac271a8c566945c6b60d8ee4c74f82284594cb))

### Fixed
- Fix sentinel typing and its uses in parser (#3396) ([`73e1550`](https://github.com/pallets/click/commit/73e155006526575548d143ef519995f540547e52))
- Ensure fish completion handles multiline help strings correctly (#3126) ([`19fd4d6`](https://github.com/pallets/click/commit/19fd4d6e18bc9fce451f92f422696b11169faa57))
- `_termui_impl.open_url()` — 'start' on Windows is a cmd built-in, not an executable (#3186) ([`c5cced7`](https://github.com/pallets/click/commit/c5cced7b3096804567688df645194e3ed3dfa88b))
- Fix readline backspace/line-wrapping on linux (#2969) ([`2468b70`](https://github.com/pallets/click/commit/2468b70997a6ec27ced4b4867954c90da3f92075))
- Fix bad merge in changes ([`3ca8f96`](https://github.com/pallets/click/commit/3ca8f96c7568ee8ec1ba604d603821d0762243f5))
