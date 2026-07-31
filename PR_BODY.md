## Summary

Adds a small, dependency-free changelog generator for the bounty request.

- `changelog.py` reads non-merge commits after the latest reachable tag.
- Commit subjects are grouped into Added, Fixed, Changed, and Removed.
- `changelog.sh` provides the requested one-command entry point.
- `.claude/skills/generate-changelog/SKILL.md` exposes the `/generate-changelog` workflow.
- The README keeps setup to three steps and documents the available flags.

## Validation

- `python -m unittest discover -s tests -v` — 3 tests passed.
- Ran against `claude-builders-bounty/claude-builders-bounty` and generated `examples/CHANGELOG.md`.
- Added a local `v0.0.0` tag to the cloned test repository and verified that only the commit after the tag appears in the generated output.

## Usage

```bash
bash changelog.sh
bash changelog.sh --version 1.2.0 --tag v1.1.0
```
