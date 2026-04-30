# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v1.4.0] — 2026-04-30

### ✨ Added
- feat: add dark mode toggle to settings panel (a3f9c12)
- feat: support GitHub OAuth login flow (b82de01)
- feat(api): add /v2/projects endpoint with pagination (c19fa44)
- feat: add CSV export for reports (d5501b3)

### 🐛 Fixed
- fix: prevent double-submit on payment form (e7712cc)
- fix(auth): handle expired refresh tokens gracefully (f441a99)
- fix: correct off-by-one in paginator (g338d20)
- hotfix: revert broken migration that dropped user_roles table (h227b11)

### 🔧 Changed
- refactor: extract EmailService into its own module (i991e08)
- perf: cache expensive SQL query in Redis (j114f77)
- chore: upgrade Next.js to 15.2 (k002c34)
- docs: update README with new environment variables (l88aa22)
- style: run prettier across all TypeScript files (m76bb11)
- ci: add GitHub Actions workflow for automated tests (n55cc00)

### 🗑️ Removed
- remove: drop legacy /v1/widgets endpoint (o44dd99)
- deprecate: remove unused `legacyAuth` flag (p33ee88)

---

[Full diff](https://github.com/example/project/compare/v1.3.2...v1.4.0)
