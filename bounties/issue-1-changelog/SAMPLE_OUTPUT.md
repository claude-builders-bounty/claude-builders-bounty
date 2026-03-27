# Sample Output

Generated from [octocat/Hello-World](https://github.com/octocat/Hello-World) (2 commits).

```markdown
# Changelog

## [2026-03-27] — 2026-03-27

### Added

- New line at end of file. --Signed off by Spaceghost (Johnneylee Jack Rollins)

### Changed

- first commit (cameronmcefee)

---
*2 commits in this release.*
```

---

Generated from a project with conventional commits and tags:

```markdown
# Changelog

## [v2.1.0] — 2026-03-27
_Changes since `v2.0.0`_

### Added
- feat(auth): add OAuth2 PKCE flow for mobile clients (alice)
- feat(api): implement rate limiting middleware (bob)
- feat(ui): add dark mode toggle to settings page (carol)
- feat(db): create migration system for schema versioning (alice)

### Fixed
- fix(auth): resolve token refresh loop on expired sessions (bob)
- fix(api): handle null response from upstream service gracefully (carol)
- fix(ui): prevent layout shift on image load (dave)

### Changed
- refactor(api): extract validation into shared middleware (alice)
- docs: update README with new environment variables (bob)
- chore(deps): bump express from 4.18 to 4.19 (dependabot)

### Removed
- deprecate: remove legacy v1 authentication endpoint (alice)

### Security
- security: sanitize user input in search queries to prevent XSS (bob)

---
*14 commits in this release.*
```
