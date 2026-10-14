# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v9.5.1] - 2026-09-01

### Fixed

- Fix `stringifyUrl()` dropping a leading `#` in the fragment identifier and throwing on some absolute URLs

## [v9.5.0] - 2026-08-06

### Changed

- Update dependencies

## [v9.4.1] - 2026-06-28

### Fixed

- Fix relative URLs with fragments

### Security

- Create security.md

## [v9.4.0] - 2026-05-28

### Added

- Add tip about `URLSearchParams`

### Changed

- Meta tweaks
- Improve performance

## [v9.3.1] - 2025-09-19

### Fixed

- Fix custom type functions with array formats

## [v9.3.0] - 2025-09-09

### Added

- Add `replacer` option to `stringify()`
- Add comprehensive test coverage for `queryString.exclude()`

### Changed

- Document supported value types for `stringify()`

### Fixed

- Fix encoded separator incorrectly splitting single values into arrays

## [v9.2.2] - 2025-07-03

### Changed

- Accept valueless parameters as `true` when using a boolean with `types` option (#410)

## [v9.2.1] - 2025-06-15

### Fixed

- Fix `stringifyUrl` not respecting passed in options

## [v9.2.0] - 2025-05-20

### Added

- Add support for `boolean` type in the `types` option (#407)

### Fixed

- Fix docs typos

## [v9.1.2] - 2025-05-02

### Added

- Add failing test for #404

### Changed

- Meta tweaks

### Fixed

- Fix `types` option with `arrayFormat: comma` and one item in array (#406)
- Fix readme typos (#397)

## [v9.1.1] - 2024-10-09

### Changed

- Meta tweaks

### Fixed

- Fix `arrayFormat` `bracket-separator` with a URL encoded value (#392)

## [v9.1.0] - 2024-07-22

### Added

- Add `types` option to the `.parse()` method (#385)
- Add tests for #381

## [v9.0.0] - 2024-02-26

### Changed

- Require Node.js 18
- Improve readme warning (#379)

### Fixed

- Fix passing empty `fragmentIdentifier` to `stringifyUrl()`

## [v8.2.0] - 2024-02-03

### Changed

- Meta tweaks
- Allow BigInt as stringifiable value in the types (#377)

## [v8.1.0] - 2022-12-20

### Changed

- Upgrade dependencies (#365)

## [v8.0.3] - 2022-12-14

### Fixed

- Fix typo in a TypeScript type

## [v8.0.2] - 2022-12-13

### Changed

- Use more compatible syntax (#361)

## [v8.0.1] - 2022-12-13

### Fixed

- Fix TypeScript compatibility

## [v8.0.0] - 2022-12-12

### Changed

- Require Node.js 14 and move to ESM

### Fixed

- Fix encoding of `fragmentIdentifier` (#355)

## [v7.1.3] - 2022-12-03

### Changed

- Update dependencies (#354)

### Fixed

- Fix CI

## [v7.1.2] - 2022-12-02

### Changed

- Update dependency (#353)
- Meta tweaks

## [v7.1.1] - 2022-02-06

### Fixed

- Fix `ParsedQuery` type to allow null in array (#338)

## [v7.1.0] - 2022-01-06

### Added

- Add support for parameters with an explicit `:list` marker (#335)

## [v7.0.1] - 2021-06-22

### Added

- Add FAQ to the readme

### Changed

- Don't encode the fragment identifier in `.pick` and `.exclude` (#320)
- Meta tweaks
- Update readme.md

## [v7.0.0] - 2021-03-18

### Added

- Add support for `arrayFormat: 'bracket-separator'` (#276)
- Implement skips for stringify array format comma (#304)

### Changed

- Meta tweaks

## [v6.14.1] - 2021-02-26

### Fixed

- Fix TypeScript type for `stringifyUrl()`

## [v6.14.0] - 2021-02-10

### Added

- Add `.pick()` and `.exclude()` (#282)

### Changed

- Ignore ending ampersand when parsing (#306)
- Update a link
- Move to GitHub Actions (#300)

## [v6.13.8] - 2020-12-30

### Changed

- Work around TypeScript bug

## [v6.13.7] - 2020-11-05

### Changed

- Allow readonly `Stringifiable[]` in `StringifiableRecord` (#291)

## [v6.13.6] - 2020-10-17

### Added

- Add tests to confirm existing number parsing behavior (#284)

### Changed

- When only receiving values with encoded array value, decode values (#287)
- Synchronize function parameter names with typings (#283)

## [v6.13.5] - 2020-10-02

### Changed

- Allow `null` and `undefined` in `Stringifiable` TypeScript type (#281)

## [v6.13.4] - 2020-09-28

### Fixed

- Fix the TypeScript types for `.stringify()` and `.stringifyUrl()` (#279)

## [v6.13.3] - 2020-09-27

### Fixed

- Fix the TypeScript type for the `.stringifyUrl()` method

## [v6.13.2] - 2020-09-13

### Fixed

- Fix the `ParsedQuery` TypeScript typ

## [v6.13.1] - 2020-06-11

### Fixed

- Fix sorting existing query params in URL when `sort` option is false (#265)

## [v6.13.0] - 2020-06-06

### Added

- Add support for parsing/stringifying fragment identifier (#222)
- Add benchmarks (#254)
- Add size badge

### Changed

- Meta tweaks

## [v6.12.1] - 2020-04-13

### Fixed

- Fix value being decoded twice with `arrayFormat` option set to `separator` (#243)

## [v6.12.0] - 2020-04-06

### Added

- Add `skipEmptyString` option (#252)

## [v6.11.1] - 2020-03-02

### Fixed

- Fix `arrayFormatSeparator` TypeScript type (#245)

## [v6.11.0] - 2020-02-13

### Changed

- Support custom array separator (#234)
- Preserve encoded commas when using `arrayFormat: 'comma'` (#236)

## [v6.10.1] - 2020-01-17

### Fixed

- Fix issue with using Rollup

## [v6.10.0] - 2020-01-16

### Added

- Add `funding` field to package.json
- Add `.stringifyUrl()` method (#217)
- Add sponsor note

### Changed

- Meta tweaks

### Removed

- Remove broken link (#232)

## [v6.9.0] - 2019-11-13

### Added

- Add option to skip keys with the value of `null` in `.stringify()` (#215)

### Changed

- Meta tweaks
- Only parse `+` to space when `decode` is true (#214)
- Tidelift tasks

## [v6.8.3] - 2019-08-31

### Changed

- Minor tweaks
- Make `parseNumbers` and `parseBooleans` options work with `arrayFormat` (#202)

## [v6.8.2] - 2019-07-26

### Changed

- Ensure empty string & spaces are parsed as string when `parseNumber: true` (#195)

## [v6.8.1] - 2019-06-21

### Fixed

- Fix using the `parseNumbers` and `parseBooleans` options together (#187)

## [v6.8.0] - 2019-06-20

### Added

- Add `parseBooleans` option to `.parse()` (#183)

### Fixed

- Fix the TypeScript types (#185)
- Fix readme examples (#181)

## [v6.7.0] - 2019-06-08

### Added

- Add `parseNumbers` option to `.parse()` (#171)

### Changed

- Meta tweaks

### Fixed

- Fix Travis

## [v6.6.0] - 2019-06-05

### Added

- Add `sort` option to `.parse()` (#177)

### Changed

- Meta tweaks
- Tidelift tasks
- Enable the repo sponsor button

### Fixed

- Fix TypeScript 3.5 compatibility (#179)

## [v6.5.0] - 2019-04-28

### Changed

- Support stringifying array containing value 0 (#173)
- Support hash in `.extract()` (#174)
- Meta tweaks

## [v6.4.2] - 2019-03-27

### Changed

- Correctly handle query strings that contain `=` (#169)

### Fixed

- Fix `split-on-first` dependency (#172)

## [v6.4.0] - 2019-03-14

### Added

- Add `comma` format to the `arrayFormat` option (#167)

### Changed

- Improve docs

### Fixed

- Fix failing test and `ParsedQuery` TypeScript type (#170)

## [v6.3.0] - 2019-03-03

### Added

- Add TypeScript definition (#168)

### Changed

- Readme tweak

### Fixed

- Fix sort example for `stringify` method (#163)
- Fix readme usage example for `sort: false` (#161)

## [v6.2.0] - 2018-10-02

### Added

- Add readme note about `create-react-app` (#156)

### Changed

- Meta tweaks
- Do not sort when `sort` option is set to false (#155)
- Support hash in `parseUrl()` (#151)
- Bump fast-check version and adapt properties (#154)

### Fixed

- Fix lint error (#149)
- Fix failing tests in Node 10 caused by wrong sort option type (#142)

## [v6.1.0] - 2018-05-03

### Added

- Add `decode` option to `.parse()` (#124)

### Changed

- Meta tweaks
- Readme tweaks

### Fixed

- Fix stringify for bracket mode with arrays containing null (#138)

## [v6.0.0] - 2018-03-14

### Changed

- Target Node.js 6 and modern browsers

## [v5.1.1] - 2018-03-14

### Changed

- Stop testing on older Node.js versions
- Allow partial imports (#125)

## [v5.1.0] - 2018-02-03

### Added

- Add `.parseUrl()` method (#104)
- Add `sort` option (#107)

### Changed

- Cleanup

## [v5.0.1] - 2017-10-24

### Changed

- Simplify a regex

### Fixed

- Fix `.extract()` for query strings containing `?` (#109)

## [v5.0.0] - 2017-07-23

### Added

- Add better component decoder - fixes #98 (#99)

### Changed

- Meta tweaks

## [v4.3.4] - 2017-04-19

### Changed

- Prevent non-array values from being wrapped in arrays (#91)

## [v4.3.3] - 2017-04-17

### Added

- Add info about falsy values to the docs (#85)

### Fixed

- Fix single bracketed array should wrap its value in an one index array (#89)

## [v4.3.2] - 2017-02-14

### Fixed

- Fix non ES5 compliant regexp (#84)

## [v4.3.1] - 2017-01-14

### Changed

- Preserve appearance order while handling multiple values (#82)

## [v4.3.0] - 2017-01-12

### Added

- Add support for bracket and index array representation (#79)

### Changed

- Minor cleanup

## [v4.2.3] - 2016-08-13

### Changed

- Trying out something new
- Improve usage example
- Meta tweaks

### Fixed

- Fix XO lint issues

## [v4.2.2] - 2016-06-12

### Changed

- Encode key when value is null (#67)

## [v4.2.1] - 2016-06-06

### Changed

- Do not sort array values while stringify (#63)
- Document support for foo=bar&foo=baz (#62)

## [v4.2.0] - 2016-05-30

### Added

- Add option to stringify without encoding

### Changed

- :arrow_up: ava@0.14.0 (#57)

## [v4.1.0] - 2016-03-30

### Changed

- Close #54 PR: add strict option. Fixes #42

## [v4.0.1] - 2016-03-28

### Changed

- Close #55 PR: Fix undefined check and tests.

## [v4.0.0] - 2016-03-26

### Changed

- Close #53 PR: support object properties - fixes #47. Fixes #47, Fixes #50
- Handle `null` and `undefined` in array - fixes #49

## [v3.0.3] - 2016-03-19

### Changed

- Revert "support object properties"

## [v3.0.2] - 2016-03-18

### Changed

- Minor tweaks
- Support object properties

## [v3.0.1] - 2016-02-27

### Changed

- Don't mutate user supplied array
- Make tests compatible with latest version of AVA

## [v3.0.0] - 2015-10-13

### Changed

- Close #36 PR: Undefined values are removed from stringified output.

## [v2.4.2] - 2015-10-04

### Changed

- Close #37 PR: Fixed raw `=`-sign, AVAfied and ES2015ified the tests. Fixes #35

## [v2.4.1] - 2015-09-04

### Added

- Add XO

### Changed

- Close #34 PR: Filter empty strings before ampersand concatenation. Fixes #31
- Close #32 PR: Failing test for stringifying an empty array.

## [v2.4.0] - 2015-07-24

### Added

- Add test for #24

### Changed

- Tweaks
- Use stricter URI encoding
- Minor readme tweaks
- Close #26 PR: add `.extract()` convenience method - fixes #15.
- Close #23 PR: Remove ampersand.
- Close #22 PR: Sort keys in `.stringify()`

### Removed

- Remove redundant trim()

## [v2.0.0] - 2015-05-04

### Changed

- Convert to vanilla commonjs

## [v1.0.1] - 2015-05-04

### Changed

- Assign to self instead of window
- Update .travis.yml
- Mention stupid Firefox bug - fixes #13

### Removed

- Remove Firefox notice

## [v1.0.0] - 2014-08-18

### Added

- Add AMD support
- Add support for multiple identical keys - fixes #4
- Add mention of nesting. Fixes #2

### Changed

- Tweaks
- Pass factory to define()
- Close GH-7: Parse hashes as well (remove # at the beginning).
- Update readme.md

## [v0.1.1] - 2013-11-16

### Added

- Add example for use with Bower and browser

### Changed

- Handle `+` in query strings correctly. Fixes #1
- Update readme.md

## [2.3.0] - 2015-06-04

### Added

- Add test for #24

### Changed

- Minor readme tweaks
- Close #26 PR: add `.extract()` convenience method - fixes #15.

### Removed

- Remove redundant trim()

## [2.2.0] - 2015-05-25

### Changed

- Close #23 PR: Remove ampersand.

## [2.1.0] - 2015-05-08

### Changed

- Close #22 PR: Sort keys in `.stringify()`
- Convert to vanilla commonjs
- Assign to self instead of window
- Update .travis.yml
- Mention stupid Firefox bug - fixes #13
- Tweaks

### Removed

- Remove Firefox notice

## [0.4.1] - 2014-07-23

### Changed

- Pass factory to define()

## [0.4.0] - 2014-05-15

### Changed

- Close GH-7: Parse hashes as well (remove # at the beginning).

## [0.3.1] - 2014-05-01

### Changed

- Update readme.md

## [0.3.0] - 2014-03-25

### Added

- Add AMD support

## [0.2.0] - 2014-03-03

### Added

- Add support for multiple identical keys - fixes #4
- Add mention of nesting. Fixes #2
- Add example for use with Bower and browser

### Changed

- Update readme.md
- Handle `+` in query strings correctly. Fixes #1
- Init

[v9.5.1]: https://github.com/sindresorhus/query-string/compare/v9.5.0...v9.5.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.5.1...HEAD
[v9.5.0]: https://github.com/sindresorhus/query-string/compare/v9.4.1...v9.5.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.5.0...HEAD
[v9.4.1]: https://github.com/sindresorhus/query-string/compare/v9.4.0...v9.4.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.4.1...HEAD
[v9.4.0]: https://github.com/sindresorhus/query-string/compare/v9.3.1...v9.4.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.4.0...HEAD
[v9.3.1]: https://github.com/sindresorhus/query-string/compare/v9.3.0...v9.3.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.3.1...HEAD
[v9.3.0]: https://github.com/sindresorhus/query-string/compare/v9.2.2...v9.3.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.3.0...HEAD
[v9.2.2]: https://github.com/sindresorhus/query-string/compare/v9.2.1...v9.2.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.2.2...HEAD
[v9.2.1]: https://github.com/sindresorhus/query-string/compare/v9.2.0...v9.2.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.2.1...HEAD
[v9.2.0]: https://github.com/sindresorhus/query-string/compare/v9.1.2...v9.2.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.2.0...HEAD
[v9.1.2]: https://github.com/sindresorhus/query-string/compare/v9.1.1...v9.1.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.1.2...HEAD
[v9.1.1]: https://github.com/sindresorhus/query-string/compare/v9.1.0...v9.1.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.1.1...HEAD
[v9.1.0]: https://github.com/sindresorhus/query-string/compare/v9.0.0...v9.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.1.0...HEAD
[v9.0.0]: https://github.com/sindresorhus/query-string/compare/v8.2.0...v9.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v9.0.0...HEAD
[v8.2.0]: https://github.com/sindresorhus/query-string/compare/v8.1.0...v8.2.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.2.0...HEAD
[v8.1.0]: https://github.com/sindresorhus/query-string/compare/v8.0.3...v8.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.1.0...HEAD
[v8.0.3]: https://github.com/sindresorhus/query-string/compare/v8.0.2...v8.0.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.0.3...HEAD
[v8.0.2]: https://github.com/sindresorhus/query-string/compare/v8.0.1...v8.0.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.0.2...HEAD
[v8.0.1]: https://github.com/sindresorhus/query-string/compare/v8.0.0...v8.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.0.1...HEAD
[v8.0.0]: https://github.com/sindresorhus/query-string/compare/v7.1.3...v8.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v8.0.0...HEAD
[v7.1.3]: https://github.com/sindresorhus/query-string/compare/v7.1.2...v7.1.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.1.3...HEAD
[v7.1.2]: https://github.com/sindresorhus/query-string/compare/v7.1.1...v7.1.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.1.2...HEAD
[v7.1.1]: https://github.com/sindresorhus/query-string/compare/v7.1.0...v7.1.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.1.1...HEAD
[v7.1.0]: https://github.com/sindresorhus/query-string/compare/v7.0.1...v7.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.1.0...HEAD
[v7.0.1]: https://github.com/sindresorhus/query-string/compare/v7.0.0...v7.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.0.1...HEAD
[v7.0.0]: https://github.com/sindresorhus/query-string/compare/v6.14.1...v7.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v7.0.0...HEAD
[v6.14.1]: https://github.com/sindresorhus/query-string/compare/v6.14.0...v6.14.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.14.1...HEAD
[v6.14.0]: https://github.com/sindresorhus/query-string/compare/v6.13.8...v6.14.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.14.0...HEAD
[v6.13.8]: https://github.com/sindresorhus/query-string/compare/v6.13.7...v6.13.8
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.8...HEAD
[v6.13.7]: https://github.com/sindresorhus/query-string/compare/v6.13.6...v6.13.7
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.7...HEAD
[v6.13.6]: https://github.com/sindresorhus/query-string/compare/v6.13.5...v6.13.6
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.6...HEAD
[v6.13.5]: https://github.com/sindresorhus/query-string/compare/v6.13.4...v6.13.5
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.5...HEAD
[v6.13.4]: https://github.com/sindresorhus/query-string/compare/v6.13.3...v6.13.4
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.4...HEAD
[v6.13.3]: https://github.com/sindresorhus/query-string/compare/v6.13.2...v6.13.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.3...HEAD
[v6.13.2]: https://github.com/sindresorhus/query-string/compare/v6.13.1...v6.13.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.2...HEAD
[v6.13.1]: https://github.com/sindresorhus/query-string/compare/v6.13.0...v6.13.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.1...HEAD
[v6.13.0]: https://github.com/sindresorhus/query-string/compare/v6.12.1...v6.13.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.13.0...HEAD
[v6.12.1]: https://github.com/sindresorhus/query-string/compare/v6.12.0...v6.12.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.12.1...HEAD
[v6.12.0]: https://github.com/sindresorhus/query-string/compare/v6.11.1...v6.12.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.12.0...HEAD
[v6.11.1]: https://github.com/sindresorhus/query-string/compare/v6.11.0...v6.11.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.11.1...HEAD
[v6.11.0]: https://github.com/sindresorhus/query-string/compare/v6.10.1...v6.11.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.11.0...HEAD
[v6.10.1]: https://github.com/sindresorhus/query-string/compare/v6.10.0...v6.10.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.10.1...HEAD
[v6.10.0]: https://github.com/sindresorhus/query-string/compare/v6.9.0...v6.10.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.10.0...HEAD
[v6.9.0]: https://github.com/sindresorhus/query-string/compare/v6.8.3...v6.9.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.9.0...HEAD
[v6.8.3]: https://github.com/sindresorhus/query-string/compare/v6.8.2...v6.8.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.8.3...HEAD
[v6.8.2]: https://github.com/sindresorhus/query-string/compare/v6.8.1...v6.8.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.8.2...HEAD
[v6.8.1]: https://github.com/sindresorhus/query-string/compare/v6.8.0...v6.8.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.8.1...HEAD
[v6.8.0]: https://github.com/sindresorhus/query-string/compare/v6.7.0...v6.8.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.8.0...HEAD
[v6.7.0]: https://github.com/sindresorhus/query-string/compare/v6.6.0...v6.7.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.7.0...HEAD
[v6.6.0]: https://github.com/sindresorhus/query-string/compare/v6.5.0...v6.6.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.6.0...HEAD
[v6.5.0]: https://github.com/sindresorhus/query-string/compare/v6.4.2...v6.5.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.5.0...HEAD
[v6.4.2]: https://github.com/sindresorhus/query-string/compare/v6.4.0...v6.4.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.4.2...HEAD
[v6.4.0]: https://github.com/sindresorhus/query-string/compare/v6.3.0...v6.4.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.4.0...HEAD
[v6.3.0]: https://github.com/sindresorhus/query-string/compare/v6.2.0...v6.3.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.3.0...HEAD
[v6.2.0]: https://github.com/sindresorhus/query-string/compare/v6.1.0...v6.2.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.2.0...HEAD
[v6.1.0]: https://github.com/sindresorhus/query-string/compare/v6.0.0...v6.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.1.0...HEAD
[v6.0.0]: https://github.com/sindresorhus/query-string/compare/v5.1.1...v6.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v6.0.0...HEAD
[v5.1.1]: https://github.com/sindresorhus/query-string/compare/v5.1.0...v5.1.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v5.1.1...HEAD
[v5.1.0]: https://github.com/sindresorhus/query-string/compare/v5.0.1...v5.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v5.1.0...HEAD
[v5.0.1]: https://github.com/sindresorhus/query-string/compare/v5.0.0...v5.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v5.0.1...HEAD
[v5.0.0]: https://github.com/sindresorhus/query-string/compare/v4.3.4...v5.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v5.0.0...HEAD
[v4.3.4]: https://github.com/sindresorhus/query-string/compare/v4.3.3...v4.3.4
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.3.4...HEAD
[v4.3.3]: https://github.com/sindresorhus/query-string/compare/v4.3.2...v4.3.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.3.3...HEAD
[v4.3.2]: https://github.com/sindresorhus/query-string/compare/v4.3.1...v4.3.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.3.2...HEAD
[v4.3.1]: https://github.com/sindresorhus/query-string/compare/v4.3.0...v4.3.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.3.1...HEAD
[v4.3.0]: https://github.com/sindresorhus/query-string/compare/v4.2.3...v4.3.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.3.0...HEAD
[v4.2.3]: https://github.com/sindresorhus/query-string/compare/v4.2.2...v4.2.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.2.3...HEAD
[v4.2.2]: https://github.com/sindresorhus/query-string/compare/v4.2.1...v4.2.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.2.2...HEAD
[v4.2.1]: https://github.com/sindresorhus/query-string/compare/v4.2.0...v4.2.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.2.1...HEAD
[v4.2.0]: https://github.com/sindresorhus/query-string/compare/v4.1.0...v4.2.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.2.0...HEAD
[v4.1.0]: https://github.com/sindresorhus/query-string/compare/v4.0.2...v4.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.1.0...HEAD
[v4.0.1]: https://github.com/sindresorhus/query-string/compare/v4.0.0...v4.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.0.1...HEAD
[v4.0.0]: https://github.com/sindresorhus/query-string/compare/v3.0.3...v4.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v4.0.0...HEAD
[v3.0.3]: https://github.com/sindresorhus/query-string/compare/v3.0.2...v3.0.3
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v3.0.3...HEAD
[v3.0.2]: https://github.com/sindresorhus/query-string/compare/v3.0.1...v3.0.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v3.0.2...HEAD
[v3.0.1]: https://github.com/sindresorhus/query-string/compare/v3.0.0...v3.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v3.0.1...HEAD
[v3.0.0]: https://github.com/sindresorhus/query-string/compare/v2.4.2...v3.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v3.0.0...HEAD
[v2.4.2]: https://github.com/sindresorhus/query-string/compare/v2.4.1...v2.4.2
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v2.4.2...HEAD
[v2.4.1]: https://github.com/sindresorhus/query-string/compare/v2.4.0...v2.4.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v2.4.1...HEAD
[v2.4.0]: https://github.com/sindresorhus/query-string/compare/v2.0.0...v2.4.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v2.4.0...HEAD
[v2.0.0]: https://github.com/sindresorhus/query-string/compare/v1.0.1...v2.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v2.0.0...HEAD
[v1.0.1]: https://github.com/sindresorhus/query-string/compare/v1.0.0...v1.0.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v1.0.1...HEAD
[v1.0.0]: https://github.com/sindresorhus/query-string/compare/v0.1.1...v1.0.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v1.0.0...HEAD
[v0.1.1]: https://github.com/sindresorhus/query-string/compare/v0.1.0...v0.1.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/v0.1.1...HEAD
[2.3.0]: https://github.com/sindresorhus/query-string/compare/2.2.0...2.3.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/2.3.0...HEAD
[2.2.0]: https://github.com/sindresorhus/query-string/compare/2.1.0...2.2.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/2.2.0...HEAD
[2.1.0]: https://github.com/sindresorhus/query-string/compare/0.4.1...2.1.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/2.1.0...HEAD
[0.4.1]: https://github.com/sindresorhus/query-string/compare/0.4.0...0.4.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/0.4.1...HEAD
[0.4.0]: https://github.com/sindresorhus/query-string/compare/0.3.1...0.4.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/0.4.0...HEAD
[0.3.1]: https://github.com/sindresorhus/query-string/compare/0.3.0...0.3.1
[Unreleased]: https://github.com/sindresorhus/query-string/compare/0.3.1...HEAD
[0.3.0]: https://github.com/sindresorhus/query-string/compare/0.2.0...0.3.0
[Unreleased]: https://github.com/sindresorhus/query-string/compare/0.3.0...HEAD
[0.2.0]: https://github.com/sindresorhus/query-string/releases/tag/0.2.0
