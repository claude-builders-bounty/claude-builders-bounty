# Changelog

All notable changes to chi will be documented in this file.

## [Unreleased] - 2026-07-17

### Added

- feat(mux): support http QUERY method ietf rfc10008 (#1132)
- feat(middleware): add text/xml and application/xml to default compressible types (#1127)
- feat: middleware.ClientIP, a replacement for middleware.RealIP (#967)
- feat(mux): support http.Request.Pattern in Go 1.23 (#986)

### Fixed

- fix(mux): use context.AfterFunc to prevent premature pool reclamation
- fix: set Request.Pattern from RoutePattern() (#1097)
- fix(middleware): add missing return in RouteHeaders empty check (#1045)
- fix: allow multiple informational status (#961)

### Changed

- ci: pin GitHub Actions to full commit SHAs (#1116)
- middleware: document printPrettyStack and harden NoColor panic test (#1131)
- Fix defaultLogEntry.Panic not respecting NoColor setting (#1050)
- Tidy build directives (#1113)
- Honor Discard() in httpFancyWriter.ReadFrom (#1110)
- Fix typo in Route doc comment (#1073)
- middleware: fix httpFancyWriter.ReadFrom double-counting bytes with Tee (#1085)
- Bump minimum Go to 1.23, always use request.Pattern (#1048)
- Apply the stringscutprefix modernizer (#1051)
- Simplify chi.walk with slices.Concat (#1053)
- Remove last uses of io/ioutil (#1054)
- add go 1.26 to ci (#1052)
- Propagate inline middlewares across mounted subrouters (#1049)
- Use strings.ReplaceAll where applicable (#1046)
- middleware: harden RedirectSlashes handler (#1044)
- Update comment about min Go version (#1023)
- update reverseMethodMap in RegisterMethod (#1022)
- Refactor to use atomic type (#1019)
- Refactor graceful shutdown example (#994)
- Bump minimum Go and use new features (#1017)
- Replace methodTypString func with reverseMethodMap (#1018)
- refactor: iterative wildcard collapsing and add test for consecutive wildcards (#1012)
- Optimize throttle middleware by avoiding unnecessary timer creation (#1011)
- fix/608 - Fix flaky Throttle middleware test by synchronizing token usage (#1016)
- Avoid potential nil dereference (#1008)
- Allow multiple whitespace between method & pattern (#1013)
- Add pathvalue example to README and implement PathValue handler. (#985)
- Correct documentation (#992)
- docs: change install code to code block (#1001)
- Make use of strings.Cut (#1005)
- Merge commit from fork
- Exclude profiler when use tinygo (#982)
- support tinygo (#978)
- Fixed the typo (#958)
- chore: delint ioutil usage (#962)
- go 1.24 (#977)
- Apply fieldalignment fixes to optimize struct memory layout (#974)
- Fix non-constant format strings in t.Fatalf (#972)
- Use strings.Cut in a few places (#971)
- Support the four most recent major versions of Go (#969)
- Revert "feat(): add CF-Connecting-IP (#908)" (#966)
- Fix `Mux.Find` not correctly handling nested routes (#954)


