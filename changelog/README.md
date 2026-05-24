# changelog.sh — Git-powered CHANGELOG generator

A single bash script that reads your git history and generates a structured,
Keep a Changelog–style `CHANGELOG.md` — categorized by conventional-commit
prefixes (`feat:`, `fix:`, `revert:`, etc.).

## 3‑Step Setup

### 1. Drop the script into your repo

```bash
curl -O https://raw.githubusercontent.com/.../changelog.sh
# or just copy changelog.sh from this directory
chmod +x changelog.sh
```

### 2. Make sure your commits follow conventional-commits

| Commit prefix        | CHANGELOG section |
|----------------------|-------------------|
| `feat:` / `feat(…):` | **Added**         |
| `fix:` / `fix(…):`   | **Fixed**         |
| `revert:` / `remove:`| **Removed**       |
| `chore:`, `docs:`, `refactor:`, `style:`, `perf:`, `test:`, `ci:`, `build:`, or anything else | **Changed** |

### 3. Run it

```bash
./changelog.sh
```

That's it — a `CHANGELOG.md` appears in your current directory.

## Options

```
Usage: changelog.sh [OPTIONS]

Options:
  -o FILE       Write output to FILE (default: CHANGELOG.md)
  -v TAG        Start changelog from TAG (default: latest git tag)
  -s RANGE      Use an arbitrary git revision range (e.g., "v1.0.0..HEAD")
  -V VERSION    Version string for the changelog header (default: "Unreleased")
  -d DIR        Path to the git repository (default: current directory)
  -h            Show help
```

## Sample Output

Below is the CHANGELOG generated from this repository's own git history
(all commits are `feat:` → **Added**):

```
# Changelog

## Unreleased (2026-05-24)

### Added

- feat: add OG image, meta tags, and improved README (3e9b52a)
- feat: add square avatar for social profiles (4052522)
- feat: Claude Builders Bounty landing page (b41377c)
- feat: initial README with bounty board (1aeae2a)
```

## Requirements

- **bash** ≥ 4.0
- **git** ≥ 2.0
- Conventional-commit style messages (plain English works too — they end up in **Changed**)

## License

MIT — same as the repo.
