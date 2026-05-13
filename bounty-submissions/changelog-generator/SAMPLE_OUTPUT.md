# Sample Output — changelog.sh

> Real execution on a test repository with conventional commits.

## Test Repository Setup

```
git init
git commit -m "feat: initial project scaffolding"
git commit -m "feat(auth): add OAuth2 authentication module"
git commit -m "feat(payment): implement Stripe checkout integration"
git commit -m "fix: resolve WebSocket race condition in real-time sync"
git commit -m "fix: correct timezone handling in cron scheduler (#42)"
git tag v1.0.0
git commit -m "refactor: migrate API layer from Express to Fastify"
git commit -m "deps: upgrade typescript from 5.3 to 5.6"
git commit -m "ci: add automated changelog generation workflow"
git commit -m "remove: drop legacy XML API endpoint"
git commit -m "security: patch CVE-2024-1234 in JWT token handler"
```

## Run (default — since last tag)

```bash
$ ./changelog.sh
📋 Commits since tag: v1.0.0
✅ Found 5 commits in range: v1.0.0..HEAD
📝 Generated CHANGELOG.md:
   Added:    0 entries
   Fixed:    0 entries
   Changed:  3 entries
   Removed:  1 entries
   Security: 1 entries
```

**Output:**
```markdown
# Changelog

## [Unreleased]

### Changed
  - ci: add automated changelog generation workflow
  - deps: upgrade typescript from 5.3 to 5.6
  - refactor: migrate API layer from Express to Fastify

### Removed
  - remove: drop legacy XML API endpoint

### Security
  - security: patch CVE-2024-1234 in JWT token handler
```

## Run (--all mode)

```bash
$ ./changelog.sh --all
📋 Including ALL commits (no tag filter)
✅ Found 10 commits in range: HEAD
📝 Generated CHANGELOG.md:
   Added:    3 entries
   Fixed:    2 entries
   Changed:  3 entries
   Removed:  1 entries
   Security: 1 entries
```

**Output:**
```markdown
# Changelog

## [Unreleased]

### Added
  - feat(payment): implement Stripe checkout integration
  - feat(auth): add OAuth2 authentication module
  - feat: initial project scaffolding

### Fixed
  - fix: correct timezone handling in cron scheduler (#42)
  - fix: resolve WebSocket race condition in real-time sync

### Changed
  - ci: add automated changelog generation workflow
  - deps: upgrade typescript from 5.3 to 5.6
  - refactor: migrate API layer from Express to Fastify

### Removed
  - remove: drop legacy XML API endpoint

### Security
  - security: patch CVE-2024-1234 in JWT token handler
```

---

_Tested on 2026-05-13 — All 5 categories verified._
