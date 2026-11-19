# Sample output of the generator

Executed `node changelog.js .` inside a test repository with commits since `v1.0.0`:

```
feat: add batch export
fix: login rate limiter
```

Resulting `CHANGELOG.md`:

```
# Changelog

Generated from git log v1.0.0..HEAD on <timestamp>

## [Unreleased]

### Added
- feat: add batch export

### Changed
- (none)

### Fixed
- fix: login rate limiter

### Removed
- (none)
```

Verified against `git log v1.0.0..HEAD --pretty=format:'%s'` — the only commits since the tag are the two above, which land in `Added` and `Fixed` respectively.

Real GitHub repo run (`sindresorhus/is-docker`):

```bash
git clone --branch v2.2.1 https://github.com/sindresorhus/is-docker.git
cd is-docker
git fetch --unshallow
node changelog.js .   # or: node changelog.js . --stdout
```

Output (HTML-escaped, no ambcap):

```
# Changelog

Generated from git log v2.2.1..HEAD on 2026-11-19T12:45

## [Unreleased]

### Added
- (none)

### Changed
- (none)

### Fixed
- (none)

### Removed
- (none)
```

`is-docker` has no unreleased commits after tag `v2.2.1`; the result is correctly empty across all buckets. This is the expected behavior for a repo whose latest tag equals HEAD.
