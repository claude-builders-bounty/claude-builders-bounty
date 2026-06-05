# Generate Changelog

Generate a structured CHANGELOG.md from git history.

**Usage:** `/generate-changelog`

**Example output:**

```markdown
## [v1.2.0] — 2026-03-15

### ✨ Added
- [`a1b2c3d`] Add user authentication with OAuth2
- [`e4f5g6h`] Implement batch image upload

### 🐛 Fixed
- [`i7j8k9l`] Fix memory leak in stream handler
- [`m0n1o2p`] Correct date formatting in reports
```

To write to a file: `/generate-changelog -o CHANGELOG.md`
