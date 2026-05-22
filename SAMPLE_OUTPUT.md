# Sample Output

Below is an example of what `generate-changelog.sh` produces for a project with conventional commits.

---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2025-01-15

### Added

- **auth**: Add OAuth2 login flow (`a1b2c3d`)
- Add user profile page (`e4f5g6h`)
- **api**: Add rate limiting middleware (`i7j8k9l`)

### Fixed

- **db**: Fix connection pool leak on timeout (`m0n1o2p`)
- Fix crash when username contains unicode (`q3r4s5t`)

### Changed

- **cli**: Refactor command parser for extensibility (`u6v7w8x`)
- Update dependencies to latest versions (`y9z0a1b`)
- **core**: Improve startup time by lazy-loading modules (`c2d3e4f`)

### Removed

- Remove deprecated v1 API endpoints (`g5h6i7j`)
- **config**: Drop support for legacy .ini format (`k8l9m0n`)

### Other

- Add integration tests for auth flow (`o1p2q3r`)
- Update contributing guidelines (`s4t5u6v`)
- Fix typo in README (`w7x8y9z`)

---

_This was generated from commits like:_

```
a1b2c3d feat(auth): Add OAuth2 login flow
e4f5g6h feat: Add user profile page
i7j8k9l add(api): Add rate limiting middleware
m0n1o2p fix(db): Fix connection pool leak on timeout
q3r4s5t fix: Fix crash when username contains unicode
u6v7w8x refactor(cli): Refactor command parser for extensibility
y9z0a1b update: Update dependencies to latest versions
c2d3e4f improve(core): Improve startup time by lazy-loading modules
g5h6i7j remove: Remove deprecated v1 API endpoints
k8l9m0n delete(config): Drop support for legacy .ini format
o1p2q3r test: Add integration tests for auth flow
s4t5u6v docs: Update contributing guidelines
w7x8y9z chore: Fix typo in README
```
