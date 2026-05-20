# Generate Changelog

A small Bash utility that creates a structured `CHANGELOG.md` from git commit history.

## Install

```bash
chmod +x changelog.sh
```

## Usage

```bash
./changelog.sh
```

This writes `CHANGELOG.md` in the current repository.

To write to a custom file:

```bash
./changelog.sh RELEASE_NOTES.md
```

To generate from a custom range:

```bash
CHANGELOG_RANGE="v1.0.0..HEAD" ./changelog.sh
```

## Output sections

The generated file contains:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The script maps common Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, and `test:` into those sections. If a section has no matching commits, it writes `No changes` so the structure stays stable.

## Sample output

Running `./changelog.sh CHANGELOG.sample.md` in this repository generates:

```markdown
# Changelog

Generated from git history. Range: `HEAD`

## Added
- Add structured changelog generator
- initial README with bounty board

## Fixed
- No changes.

## Changed
- No changes.

## Removed
- No changes.
```
