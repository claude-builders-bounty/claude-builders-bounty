# Sample output (real repository)

Run against `sindresorhus/yocto-queue`, a public repo with tags:

```bash
git clone --depth 60 https://github.com/sindresorhus/yocto-queue
cd yocto-queue
bash changelog.sh --from v1.2.0 --version 1.3.0 --out CHANGELOG.md
```

Produced:

```markdown
## [1.3.0] - 2026-11-12

### Changed
- Meta tweaks  (72a8fa9)
- 1.2.2  (b07eac0)
- 1.2.1  (ce72d41)
- Do not ignore `undefined` values while draining (#13)  (ee91589)

### Fixed
- Clean up tail reference when queue empties  (8aead27)
```
