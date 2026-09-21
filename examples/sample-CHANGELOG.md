# Changelog

All notable changes to **expressjs/express** are documented here.

## [Unreleased] — 2026-09-21

_Generated from commits since `v5.2.1`._

### Added

- allow conditional revalidation for QUERY requests (#7366) (`ae6dd37`)
- Allow passing null or undefined as the value for options in app.render (#6903) (`c9ecf7b`)
- do not modify the Content-Type twice when sending strings (#6991) (`a479419`)
- 📝 add note to history (`9eb7001`)

### Fixed

- **res.send**: preserve ETag generation with Transfer-Encoding (#7459) (`9a34acf`)
- deps: bump body-parser to ^2.3.0 to fix CVE-2026-12590 (#7390) (`8ba0c07`)
- **res.send**: add Content-Length header only if Transfer-Encoding is not present (#4893) (`18e5985`)
- replace deprecated trimRight() with trimEnd() (#7265) (`9d8223d`)
- fixed typo in history.md (#7191) (`f873ac2`)
- bump qs minimum to ^6.14.2 for CVE-2026-2391 (#7057) (`925a1df`)
- search example to support Redis v4+ and Express 4/5 (#6274) (`d127723`)
- enhance req.acceptsCharsets method (#6088) (`6cd404e`)

### Changed

- add npm staged publication with dist-tag support (#7464) (`3ce6d0e`)
- fix capitalization of GitHub Discussions in Readme (#7426) (`53d4a0d`)
- **deps-dev**: bump morgan from 1.11.0 to 1.12.0 (#7461) (`bed501c`)
- **deps**: bump the github-actions group with 5 updates (#7462) (`4e65ec9`)
- **deps-dev**: bump hbs from 4.2.1 to 4.3.0 (#7450) (`4fe723d`)
- group github actions updates (#7460) (`c35284e`)
- **deps**: bump github/codeql-action/upload-sarif (#7400) (`023767f`)
- **deps**: bump coverallsapp/github-action from 2.3.7 to 2.3.8 (#7399) (`2574a53`)
- **res.location**: clean up deprecated back string references (#7406) (`91d333b`)
- **deps**: bump actions/checkout from 7.0.0 to 7.0.1 (#7403) (`28f732e`)
- **deps-dev**: bump hbs from 4.2.0 to 4.2.1 (#7152) (`a371447`)
- **deps-dev**: bump morgan from 1.10.1 to 1.11.0 (#7353) (`ba00676`)
- **deps**: bump actions/checkout from 6.0.2 to 7.0.0 (#7345) (`5175d2f`)
- use the new logo (#7316) (`66878d3`)
- Upgrade `content-disposition` (#7233) (`59e205a`)
- **deps**: bump github/codeql-action from 4.35.2 to 4.36.0 (#7297) (`b3004cb`)
- Improve error logging by logging full error object (#6464) (`90ec620`)
- Upgrade `content-type` (#7234) (`cb19f04`)
- deps: bump qs minimum to 6.15.2 (#7305) (`a08da78`)
- **deps**: bump github/codeql-action from 4.35.1 to 4.35.2 (#7212) (`dae209a`)
- **deps**: bump actions/upload-artifact from 7.0.0 to 7.0.1 (#7211) (`777001a`)
- **deps**: bump actions/setup-node from 6.3.0 to 6.4.0 (#7210) (`64576bd`)
- build express with node.js v26 (#7218) (`f5c159b`)
- ensure safe config in the npmrc (#7144) (`2eae22b`)
- **deps**: bump github/codeql-action from 4.32.4 to 4.35.1 (#7150) (`6340c1e`)
- **deps**: bump actions/setup-node from 6.2.0 to 6.3.0 (#7149) (`8cc3afa`)
- **deps**: bump actions/download-artifact from 8.0.0 to 8.0.1 (#7148) (`e7fd63a`)
- update npm install docs URL in Readme.md (#7159) (`8e022ed`)
- replace dummy with placeholder in example comments (#7064) (`6c4249f`)
- **deps**: bump actions/upload-artifact from 6.0.0 to 7.0.0 (#7074) (`06e2367`)
- **deps**: bump actions/download-artifact from 7.0.0 to 8.0.0 (#7073) (`e3b962c`)
- **deps**: bump github/codeql-action from 4.32.0 to 4.32.4 (#7072) (`411061d`)
- include edge case tests for `res.type()` (#7037) (`b4ab7d6`)
- fix README security policy link (#7029) (`c4cc78b`)
- **deps**: bump github/codeql-action from 4.31.9 to 4.32.0 (#7013) (`1140301`)
- **deps**: bump actions/setup-node from 6.1.0 to 6.2.0 (#7012) (`c76ed5a`)
- **deps**: bump actions/checkout from 6.0.1 to 6.0.2 (#7011) (`2d4192e`)
- Add @GroophyLifefor to the triage team (#6995) (`66404b3`)
- add test for normalizeType fallback when mime lookup fails (#6894) (`6b7ccfc`)
- added unit tests for utils.compileETag to cover valid and invalid inputs (#6534) (`912893c`)
- fix JSDoc for req.accepts() return value and parameter format (#6936) (`ae265a9`)
- Polish HTML structure of the response in the res.redirect() function (#5167) (`9a3f7ff`)
- add @krzysdz to the triage team (#6482) (`2cd372e`)
- **deps**: bump actions/setup-node from 6.0.0 to 6.1.0 (#6962) (`04d3a49`)
- **deps**: bump actions/checkout from 6.0.0 to 6.0.1 (#6963) (`bc7d155`)
- deps: qs@^6.14.1 (`00bb633`)
- **deps**: bump github/codeql-action from 4.31.6 to 4.31.9 (#6964) (`3c0ad4e`)
- **deps**: bump actions/upload-artifact from 5.0.0 to 6.0.0 (#6965) (`4ae96bd`)
- **deps**: bump actions/download-artifact from 6.0.0 to 7.0.0 (#6961) (`3e81873`)
- fix security.md link to point to security tab (`b5aae87`)
- use global Security policy (`b8fc000`)
- add @rxmarbles to triagers (#6953) (`c2fb76e`)

### Removed

- remove dead link from Readme (#7136) (`e509919`)
- Remove duplicate tests in res.location and res.jsonp (#6996) (`9c85a25`)
- remove benchmarks directory (#6992) (`5a4568a`)
