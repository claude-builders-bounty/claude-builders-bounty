# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased (since v1.12.0)] — 2026-10-02

### Added
- add support for the HTTP QUERY method (RFC 10008) (#4806) (`b1f77cf`)
- add QUERY method shortcut for RFC 10008 (#4830) (`2a1a14f`)
- add Scheme() with proper reverse proxy support (#4655) (`96ece6a`)
- add PDF renderer and tests (#4491) (`052d1a7`)

### Fixed
- load Keys under the mutex in Copy (#4854) (`1bd0ecf`)
- reset skipped-nodes stack on getValue entry to prevent slice overflow panic [#4818] (#4819) (`3b08cd7`)
- add default ReadHeaderTimeout to http.Server in Run methods (#4800) (`d8f2d58`)
- handle missing HTML renderer (#4805) (`5c6a15f`)
- patch x/crypto vulnerabilities (#4832) (`bc141b4`)
- bump golang.org/x/net and golang.org/x/text to patched versions (#4807) (`8dd2011`)
- skip chmod on pre-existing dirs in SaveUploadedFile (#4702) (`d9307db`)
- record recovered panics in c.Errors (#4698) (`4a3eb31`)
- Copy() copies Errors and Accepted fields (#4695) (`293ad7e`)
- panic on Hijack/CloseNotify when wrapper unsupported (#4645) (`d75fcd4`)

### Changed
- fix SecureJSON default prefix and default-binding example output (#4861) (`43fe48e`)
- fix the graceful shutdown example (#4809) (`8ad9f9c`)
- bump github.com/stretchr/testify to v1.12.1 (#4822) (`05b14df`)
- align function comments with names (#4814) (`e318c6a`)
- fix stale comparison base and invalid config (#4823) (`3329b63`)
- document panic conditions in Handle, StaticFS, and Bind (#4797) (`b52df1f`)
- fix malformed comment in cleanPath (#4723) (`dcaa429`)
- bump the actions group across 1 directory with 4 updates (#4787) (`00cfe5a`)
- fix `BindXML` comment referencing nonexistent `binding.BindXML` (#4717) (`34dac20`)
- update validator library to version 10.30.3 (#4707) (`03f3e42`)
- use t.TempDir() for SaveUploadedFile permission test on WSL (#4709) (`da1e108`)
- add tests for Flush() with and without http.Flusher (#4699) (`074b669`)
- bump github.com/quic-go/quic-go to v0.60.0 (#4713) (`2e4d4f3`)
- bump golang.org/x/net to v0.55.0 (#4678) (`8d0468f`)
- align inline comments in GetPostForm example (#4675) (`88c4263`)
- optimize error message concatenation in default_validator (#4685) (`c79f5d4`)
- bump the actions group across 1 directory with 2 updates (#4640) (`5f4f964`)
- add regression tests for HandleContext with NoRoute (#4571) (`d3ffc99`)
- update benchmark results with latest data (#4583) (`ecd26c8`)
- replace AUTHORS.md with link to GitHub contributors page (#4582) (`a749e4d`)
- update benchmark report with Gin v1.12.0 results (#4581) (`65d1c47`)
- use the built-in max/min to simplify the code (#4576) (`6d88072`)
- upgrade Go dependencies and CI action versions (#4580) (`48667a2`)
- reorganize doc.md TOC into thematic groups (#4579) (`d467221`)
- bump aquasecurity/trivy-action in the actions group (#4557) (`3e44fdc`)
- modify test folder and test command in Makefile (#4465) (`cb2b764`)
- update license period (#4130) (`a39670f`)
- revise and expand Gin 1.12.0 release announcement (#4554) (`ff00c01`)

