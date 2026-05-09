# Changelog Generator

A zero-dependency Node.js script that automatically generates a structured `CHANGELOG.md` from your git commit history. It follows the Conventional Commits specification to categorize changes (Features, Fixes, Documentation, etc.).

## Features

- **Zero Dependencies:** Uses only built-in Node.js modules (`fs`, `child_process`, `path`).
- **Conventional Commits:** Automatically parses and groups commits into sections (`Features`, `Fixes`, `Documentation`, `Performance`, `Refactors`, `Other`).
- **Tag Aware:** Only parses commits made since the last git tag. If no tag exists, it parses all commits.
- **Smart Appending:** Prepends new changes to the top of an existing `CHANGELOG.md` without overwriting historical data.

## Usage

1. Ensure you have Node.js installed.
2. Drop `index.js` into your project or install it globally.
3. Run the script from the root of your git repository:

```bash
node index.js
```

Or if you've linked it:

```bash
generate-changelog
```

### Options

- `--dry-run`: Prints the generated markdown to the console without modifying any files.
  ```bash
  node index.js --dry-run
  ```
- `--output <path>`: Specifies a custom output file path (defaults to `CHANGELOG.md`).
  ```bash
  node index.js --output docs/CHANGELOG.md
  ```

## Automated GitHub Action

This package includes a ready-to-use GitHub Action workflow (`changelog-action.yml`).

If you place this YAML file in your repository's `.github/workflows/` directory, it will automatically run the script, generate a changelog, and push the updated `CHANGELOG.md` back to your repository whenever a new `v*` tag is pushed.

## How it works

1. It runs `git describe --tags --abbrev=0` to find the latest tag.
2. It fetches commits using `git log` formatted to extract the hash, message, author, and date.
3. It parses the commit messages using a regex matching the `type(scope): description` format.
4. It maps the types to readable categories.
5. It generates markdown and safely injects it at the top of your `CHANGELOG.md`.

## Example Output

```markdown
## Unreleased (since v1.2.0) - 2026-05-09

### Features
- **auth:** add oauth2 support (a1b2c3d) by @johndoe
- allow custom themes (e4f5g6h) by @janedoe

### Fixes
- **ui:** resolve overflow issue on mobile (i7j8k9l) by @johndoe

### Documentation
- update readme installation steps (m0n1o2p) by @janedoe
```
