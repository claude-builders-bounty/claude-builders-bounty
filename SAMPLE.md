🔍 Scanning commits: 00bb633ca6d1970e02d9ea893384efa155f15513..HEAD
# Changelog

## [Unreleased] — 2026-05-12

_Commits since: initial commit_

### Added

- feat: Allow passing null or undefined as the value for options in app.render (#6903) (c9ecf7b, @AkaHarshit)
- feat: do not modify the Content-Type twice when sending strings (#6991) (a479419, @Sebastian Beltran)

### Fixed

- fixed typo in history.md (#7191) (f873ac2, @Open Source Zeal)
- fix: bump qs minimum to ^6.14.2 for CVE-2026-2391 (#7057) (925a1df, @Dave Tashner)
- fix: search example to support Redis v4+ and Express 4/5 (#6274) (d127723, @Viny Brun Kriesang)

### Changed

- build(deps): bump github/codeql-action from 4.32.4 to 4.35.1 (#7150) (6340c1e, @dependabot[bot])
- build(deps): bump actions/setup-node from 6.2.0 to 6.3.0 (#7149) (8cc3afa, @dependabot[bot])
- build(deps): bump actions/download-artifact from 8.0.0 to 8.0.1 (#7148) (e7fd63a, @dependabot[bot])
- docs: update npm install docs URL in Readme.md (#7159) (8e022ed, @Vansh Sharma)
- docs: remove dead link from Readme (#7136) (e509919, @Ayush Shukla)
- docs: replace dummy with placeholder in example comments (#7064) (6c4249f, @Sam Tucker-Davis)
- build(deps): bump actions/upload-artifact from 6.0.0 to 7.0.0 (#7074) (06e2367, @dependabot[bot])
- build(deps): bump actions/download-artifact from 7.0.0 to 8.0.0 (#7073) (e3b962c, @dependabot[bot])
- build(deps): bump github/codeql-action from 4.32.0 to 4.32.4 (#7072) (411061d, @dependabot[bot])
- test: include edge case tests for `res.type()` (#7037) (b4ab7d6, @Ishita Singh)
- docs: fix README security policy link (#7029) (c4cc78b, @Pavan Shinde)
- build(deps): bump github/codeql-action from 4.31.9 to 4.32.0 (#7013) (1140301, @dependabot[bot])
- build(deps): bump actions/setup-node from 6.1.0 to 6.2.0 (#7012) (c76ed5a, @dependabot[bot])
- build(deps): bump actions/checkout from 6.0.1 to 6.0.2 (#7011) (2d4192e, @dependabot[bot])
- docs: Add @GroophyLifefor to the triage team (#6995) (66404b3, @Sebastian Beltran)
- test: add test for normalizeType fallback when mime lookup fails (#6894) (6b7ccfc, @Ayoub Mabrouk)
- chore: remove benchmarks directory (#6992) (5a4568a, @Sebastian Beltran)
- test: added unit tests for utils.compileETag to cover valid and invalid inputs (#6534) (912893c, @sukdev24)
- docs: fix JSDoc for req.accepts() return value and parameter format (#6936) (ae265a9, @Marcos Molina)
- Polish HTML structure of the response in the res.redirect() function (#5167) (9a3f7ff, @Bernice Wu)
- docs: add @krzysdz to the triage team (#6482) (2cd372e, @Sebastian Beltran)
- build(deps): bump actions/setup-node from 6.0.0 to 6.1.0 (#6962) (04d3a49, @dependabot[bot])
- build(deps): bump actions/checkout from 6.0.0 to 6.0.1 (#6963) (bc7d155, @dependabot[bot])

### Removed

- Remove duplicate tests in res.location and res.jsonp (#6996) (9c85a25, @Murat Kirazkaya)

---

**Total:** 29 commits — 2 added · 3 fixed · 23 changed · 1 removed
