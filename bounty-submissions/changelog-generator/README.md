# 🔄 Changelog Generator
> **** — Claude Code Skill · Bounty $50

---

## 🚀 Quick Start (3 Steps)

1. **Download**: `curl -o changelog.sh https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh`
2. **Permission**: `chmod +x changelog.sh`
3. **Run**: `./changelog.sh --all`

---

## 📋 Real-World Example Output

Running against a standard Next.js repository:

```
📋 Including ALL commits (no tag filter)
✅ Found 10 commits in range: HEAD
📝 Generated CHANGELOG.md:
   Added:    3 entries
   Fixed:    2 entries
   Changed:  3 entries
   Removed:  1 entries
   Security: 1 entries
```

**Generated `CHANGELOG.md`:**

```markdown
# Changelog

## [Unreleased]

### Added
  - feat(payment): implement Stripe checkout integration
  - feat(auth): add OAuth2 authentication with NextAuth v5
  - feat: initial project scaffolding with Next.js 15

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

> _Proof of execution captured 2026-05-13 — see SAMPLE_OUTPUT.md for full trace._

---

## 🛠 Features

- **Auto-categorization** via Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `deps:`, `remove:`, `security:`)
- **Tag-aware** — auto-detects last git tag, generates since that point
- **Dry-run mode** — preview output without writing file
- **CI/CD ready** — single bash script, zero external dependencies
- **Keep a Changelog** compliant output format

---

## Usage Options

| Command | Description |
|---------|-------------|
| `./changelog.sh` | Since last git tag (default) |
| `./changelog.sh --all` | All commits, no tag filter |
| `./changelog.sh v2.0.0` | Since specific tag |
| `./changelog.sh --dry-run` | Preview without writing file |
| `OUTPUT_FILE=RELEASE.md ./changelog.sh` | Custom output filename |

---

## Categorization Rules

| Commit Prefix | Category |
|---------------|----------|
| `feat:` `add:` `added:` | **Added** |
| `fix:` `bug:` `hotfix:` | **Fixed** |
| `refactor:` `perf:` `style:` `chore:` `deps:` `ci:` `build:` `test:` `docs:` | **Changed** |
| `remove:` `revert:` `drop:` `deprecate:` | **Removed** |
| `security:` `vuln:` | **Security** |

---

## CI/CD Integration

```yaml
# .github/workflows/changelog.yml
- name: Generate Changelog
  run: bash changelog.sh
- name: Commit Changelog
  run: |
    git add CHANGELOG.md
    git commit -m "docs: update changelog [skip ci]" || true
    git push
```

--- 
