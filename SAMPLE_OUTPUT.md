# Changelog

All notable changes to **expressjs/express** are documented here.

## [Unreleased] — 2026-09-21

_Generated from commits since `v5.2.1`._

This sample demonstrates categorization from real git history, including issue/PR references and short commit IDs.

### Added

- allow conditional revalidation for QUERY requests (#7366) (`ae6dd37`)
- Allow passing null or undefined as the value for options in app.render (#6903) (`c9ecf7b`)
- do not modify the Content-Type twice when sending strings (#6991) (`a479419`)
- 📝 add note to history (`9eb7001`)

### Fixed

- **res.send**: preserve ETag generation with Transfer-Encoding (#7459) (`9a34acf`)
- deps: bump body-parser to ^2.3.0 to fix CVE-2026-12590 (#7390) (`8ba0c07`)
- replace deprecated trimRight() with trimEnd() (#7265) (`9d8223d`)
- bump qs minimum to ^6.14.2 for CVE-2026-2391 (#7057) (`925a1df`)
- enhance req.acceptsCharsets method (#6088) (`6cd404e`)

### Changed

- add npm staged publication with dist-tag support (#7464) (`3ce6d0e`)
- **deps**: bump the github-actions group with 5 updates (#7462) (`4e65ec9`)
- Improve error logging by logging full error object (#6464) (`90ec620`)
- build express with node.js v26 (#7218) (`f5c159b`)

### Removed

- remove dead link from Readme (#7136) (`e509919`)
- Remove duplicate tests in res.location and res.jsonp (#6996) (`9c85a25`)
- remove benchmarks directory (#6992) (`5a4568a`)
