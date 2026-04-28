## [Unreleased] — 2026-04-27

### Added
- feat: export encode function from buildURL helper (#6897) (`a88f748`)
- feat: add ECONNREFUSED error code constant to AxiosError (#10680) (`a501f10`)

### Fixed
- fix(fetch): preserve abort reasons in fetch adapter (#10806) (`2344aab`)
- fix(index): add create to index exports (#6460) (`bef4868`)
- fix: missing beforeRedirect requestDetails argument (#6241) (`caa3497`)
- fix(types): export RawAxiosHeaders to fix TS2742 in consumers (#6389) (`8032488`)
- fix(types): align cjs cancelToken types (#7414) (`b072ee8`)
- fix(fetch-adapter): set User-Agent header to match http adapter (#10772) (`c918e85`)
- fix: transformRequest input typing (#10745) (`694f1ec`)
- fix(dispatchRequest): attach response to AxiosError on JSON parse failure (#10724) (`bd3816b`)
- fix(parseProtocol): fix regex to require colon in protocol separator (#10729) (`f2dc449`)
- fix(xhr): unsubscribe cancelToken and signal on error, timeout, and abort paths (#10787) (`640458d`)
- fix: close redirect listiner chanin correctly to no longer stack (#10800) (`e6a6241`)
- fix: clear stale header on redirect when target is no-proxy (#10794) (`afca61a`)
- fix: incorrect assumption on test (#10796) (`d8165e9`)
- fix: fetch adaptor is not enforcing max body or content length (#10795) (`e5540dc`)

### Changed
- chore: added clarifying docs for the type change (#10804) (`25387ae`)
- docs(readme): add timeout guidance to first async example (#10759) (`2f89ce6`)
- docs: update sponsors (`cc9aa2f`)
- chore: boundary error (#7419) (`2a08578`)
- refactor: modernize utils and xhr adapter using ES6 features (#10588) (`767b975`)
- test: fix Win32 platform support; (#10791) (`fba7fcc`)
- chore: update changelog and packages (#10790) (`de1a810`)
- chore(deps): bump the github-actions group with 3 updates (#10785) (`b2890f8`)

### Removed
- revert: transformrequest typing 10745 (#10810) (`d9b941c`)
