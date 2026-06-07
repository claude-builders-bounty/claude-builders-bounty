# Changelog

## [v2.1.0] – 2026-06-06

### ✨ Added

- OAuth login via GitHub and Google ([`a1b2c3d`](https://github.com/acme/myapp/commit/a1b2c3d4e5f6))
- Dark mode toggle with system preference detection ([`b2c3d4e`](https://github.com/acme/myapp/commit/b2c3d4e5f6a7))
- Export dashboard data to CSV ([`c3d4e5f`](https://github.com/acme/myapp/commit/c3d4e5f6a7b8))
- Rate limiting on all public API endpoints ([`d4e5f6a`](https://github.com/acme/myapp/commit/d4e5f6a7b8c9))

### 🐛 Fixed

- Session cookie not cleared on logout in Safari ([`e5f6a7b`](https://github.com/acme/myapp/commit/e5f6a7b8c9d0))
- Pagination off-by-one on the last page ([`f6a7b8c`](https://github.com/acme/myapp/commit/f6a7b8c9d0e1))
- Stripe webhook silently dropping events with non-ASCII metadata ([`a7b8c9d`](https://github.com/acme/myapp/commit/a7b8c9d0e1f2))

### 🔧 Changed

- Upgraded Next.js from 14 to 15 and migrated to App Router ([`b8c9d0e`](https://github.com/acme/myapp/commit/b8c9d0e1f2a3))
- Replaced Prisma with Drizzle ORM — query performance improved ~40% ([`c9d0e1f`](https://github.com/acme/myapp/commit/c9d0e1f2a3b4))
- Moved API keys to environment variables validated at boot ([`d0e1f2a`](https://github.com/acme/myapp/commit/d0e1f2a3b4c5))
- CI now runs on Node 22 LTS ([`e1f2a3b`](https://github.com/acme/myapp/commit/e1f2a3b4c5d6))

### 🗑️ Removed

- Legacy REST v1 endpoints (deprecated since v1.8.0) ([`f2a3b4c`](https://github.com/acme/myapp/commit/f2a3b4c5d6e7))
- Unused `pages/` directory after App Router migration ([`a3b4c5d`](https://github.com/acme/myapp/commit/a3b4c5d6e7f8))

## [v2.0.1] – 2026-05-30

### 🐛 Fixed

- Build failure on Windows due to path separator in glob pattern ([`b4c5d6e`](https://github.com/acme/myapp/commit/b4c5d6e7f8a9))
