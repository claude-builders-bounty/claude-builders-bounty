<!-- Source repo: https://github.com/sindresorhus/conf  |  Command: bash changelog.sh  |  Range: v15.1.0..HEAD  |  Entries: 12 -->
# Changelog

Generated 2026-10-11 from git history (v15.1.0..HEAD).

## Added
  - Add `cache` option (d5748fc)
  - Add comment clarifying that umask reduces effective file permissions (b1e8582)

## Fixed
  - Fix docs (916809f)

## Changed
  - Document how to get types out of the `schema` option (83e2671)
  - Do not run migrations for a store that does not exist yet (d22f423)
  - Stop exposing the internal key through the public API (3e04d61)
  - Throw when `rootSchema` contains a `properties` key (7240281)
  - Stop migration ranges from bricking the store (f957559)
  - Make `reset()` work with dot-notation keys (f9b13df)
  - Throw when `get()` is called with a non-string key (54829ff)
  - Meta tweaks (0c66c37)
  - Update readme (a95630d)

