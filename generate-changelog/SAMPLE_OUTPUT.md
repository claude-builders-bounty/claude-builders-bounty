# Sample Output

Tested on `ritesh-1918/HELPDESK.AI` after fetching its `gssoc` branch and tags:

```bash
bash generate-changelog/changelog.sh v1.0.1-mobile
```

Excerpt:

```markdown
# Changelog

## [Unreleased] - 2026-05-28

_Generated from git history since v1.0.1-mobile._

### Added

- feat: implement real-time AI processing stream and fix ticket creation 405 error (9e50e3f)
- feat: add backend readiness healthcheck (c88ced5)
- feat: override weak ML predictions with LLM categorization for multilingual support (954b1aa)

### Fixed

- fix: resolve github action deployment error and missing favicon (7c42140)
- fix: use jsonable_encoder to prevent json.dumps crash on numpy types in SSE stream (c29bbeb)
- fix: handle classifier_v3 fallback gracefully to prevent confidence keyerror (9390c3e)

### Changed

- chore: add lint-staged config to run ESLint on staged frontend files (a1e8a77)

### Removed

- No entries.
```
