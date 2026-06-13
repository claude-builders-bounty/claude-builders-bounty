# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from commits since the last Git tag.

## Setup

1. Copy `skills/generate-changelog/` into the target repository.
2. Run `bash skills/generate-changelog/changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

## Usage

```bash
bash skills/generate-changelog/changelog.sh
```

Custom output path and release name:

```bash
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md --version 1.4.0
```

## Categories

| Category | Commit signals |
| --- | --- |
| Added | `feat`, `add`, `new`, `create`, `introduce` |
| Fixed | `fix`, `bug`, `patch`, `resolve`, `repair` |
| Removed | `remove`, `delete`, `drop`, `deprecate` |
| Changed | everything else, including `docs`, `refactor`, `test`, `chore`, and `perf` |

## Sample

See `examples/sample-output.md` for output generated from a real Git repository.
