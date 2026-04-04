# Changelog

## Unreleased

### ✨ Features

- Automatic commit categorization from git history (`a1b2c3d`)
- Support for conventional commit format parsing (`e4f5g6h`)
- Multiple output formats: Markdown and JSON (`i7j8k9l`)
- CLI parameters: `--format`, `--since`, `--all` (`m1n2o3p`)
- GitHub Actions workflow for CI/CD automation (`q4r5s6t`)

### 🐛 Bug Fixes

- Handle repositories with no tags gracefully (`u7v8w9x`)
- Fix special characters in commit messages breaking output (`y1z2a3b`)
- Correct date formatting across different locales (`c4d5e6f`)

### 📝 Documentation

- README with 3-step setup instructions (`g7h8i9j`)
- SKILL.md with full usage reference (`k1l2m3n`)
- Sample outputs for both Markdown and JSON formats (`o4p5q6r`)

### ♻️ Refactoring

- Restructured categorization logic for 7 commit types (`s7t8u9v`)
- Improved conventional commit prefix stripping (`w1x2y3z`)

### 🔧 Chores

- Added GitHub Actions workflow template (`a4b5c6d`)
- Project initialization and structure (`e7f8g9h`)

---

## JSON Output Sample

When using `--format=json`, the output looks like:

```json
{
  "version": "Unreleased",
  "generated": "2026-04-04T09:37:00Z",
  "categories": {
    "features": [
      {"hash": "a1b2c3d", "message": "Automatic commit categorization from git history"},
      {"hash": "e4f5g6h", "message": "Support for conventional commit format parsing"},
      {"hash": "i7j8k9l", "message": "Multiple output formats: Markdown and JSON"}
    ],
    "bug_fixes": [
      {"hash": "u7v8w9x", "message": "Handle repositories with no tags gracefully"},
      {"hash": "y1z2a3b", "message": "Fix special characters in commit messages"}
    ],
    "documentation": [
      {"hash": "g7h8i9j", "message": "README with 3-step setup instructions"}
    ]
  },
  "stats": {
    "total": 14,
    "features": 5,
    "bug_fixes": 3,
    "documentation": 3,
    "styling": 0,
    "refactoring": 2,
    "tests": 0,
    "chores": 2,
    "other": 0
  }
}
```
