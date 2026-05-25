---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the last tag
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## When to use

- Before a release or version bump
- When preparing a Pull Request for review
- After merging several features or fixes

## How it works

1. Finds the most recent git tag (or uses the initial commit)
2. Scans all commits since that tag
3. Categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**, **Documentation**, **Tests**, **Performance**, **Security**, **Style**, **CI/CD**
4. Writes a clean `CHANGELOG.md` to the project root

## Usage

```
/generate-changelog
```

Or standalone:

```bash
bash skills/changelog/changelog.sh
```

## Categorization Rules

| Conventional Commit | Section |
|---|---|
| `feat:`, `add:`, `new:`, `implement:` | Added |
| `fix:`, `bug:`, `hotfix:`, `patch:` | Fixed |
| `change:`, `update:`, `refactor:`, `improve:` | Changed |
| `remove:`, `deprecate:`, `delete:`, `drop:` | Removed |
| `docs:`, `document:` | Documentation |
| `perf:`, `optimize:`, `speed:` | Performance |
| `security:`, `vuln:`, `cve:` | Security |
| `style:`, `format:`, `lint:` | Style |
| `test:`, `spec:`, `coverage:` | Tests |
| `ci:`, `build:`, `docker:`, `deploy:` | CI/CD |
