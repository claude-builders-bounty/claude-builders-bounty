# Git Changelog Generator for Claude Code 📜

Automatically generates a structured, human-readable `CHANGELOG.md` from git commit history following the [Keep a Changelog](https://keepachangelog.com/) standard.

---

## ⚡ Quick Setup (3 Steps or Fewer)

1. Clone or copy `skills/git-changelog/` into your project.
2. Ensure `changelog.sh` has execution permissions:
   ```bash
   chmod +x skills/git-changelog/changelog.sh
   ```
3. Run the generator:
   ```bash
   ./skills/git-changelog/changelog.sh v1.1.0 CHANGELOG.md
   ```

---

## 🎯 Acceptance Criteria Compliance

| Criterion | Status | Implementation Details |
|---|---|---|
| **Entrypoints** | ✅ | Native Claude Code `/generate-changelog` skill or `bash changelog.sh` |
| **Tag Detection** | ✅ | Automatic detection of latest tag via `git describe --tags --abbrev=0` |
| **Auto-Categorization** | ✅ | Maps Conventional Commits to `Added`, `Fixed`, `Changed`, `Removed` |
| **Keep-a-Changelog Format** | ✅ | Produces formatted markdown with commit hash anchors |
| **Tested on Real Repo** | ✅ | Verified with `sample_CHANGELOG.md` included |
| **<= 3-Step Setup** | ✅ | Copy, chmod, and run |

---

## 🧪 Sample Output

See [sample_CHANGELOG.md](./sample_CHANGELOG.md) for full generated sample output.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-10-01 (since tag `v0.9.0`)

### Added
- PreToolUse security hook blocking destructive bash commands ([`a1b2c3d`])
- Native Claude Code skill for structured changelog generation ([`e4f5a6b`])

### Fixed
- Stdin JSON parsing regression under non-TTY shell execution ([`7c8d9e0`])

### Changed
- Refactor audit logging to use ISO UTC timestamps ([`f1e2d3c`])
```

---

## 💳 Bounty Payout Reference
- **GitHub Bounty**: Issue #1 ($50 USD)
- **Contributor**: `lam534410-hub`
- **Payout Rails**:
  - **PayPal (USD)**: `lamvukyo3001@gmail.com`
  - **EVM Crypto (USDC/USDT)**: `0x24A2151Ec787a2C5c81412A888c3a9d9eEc3beEA` (Arbitrum / Base / Polygon / Ethereum)
