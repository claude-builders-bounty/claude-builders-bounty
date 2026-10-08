# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from Git history with one Bash command.

## Setup — 3 steps
1. Copy `changelog.sh` into a Git repository.
2. Make it executable if needed: `chmod +x changelog.sh`.
3. Run `bash changelog.sh`.

The script uses the latest tag reachable from `HEAD` as the baseline and reads commits after that tag. If no reachable tag exists, it safely uses the reachable repository history instead of returning an empty success.

Commit subjects are grouped into `Added`, `Fixed`, `Changed`, and `Removed`. Conventional Commit prefixes with optional scopes are supported, plus simple case-insensitive verb fallbacks such as `add`, `fix`, and `remove`.

## Verification

- Bash syntax check: PASS.
- Synthetic tagged repository: PASS for all four categories.
- Real public GitHub repository: `pallets/flask`.
- Tested HEAD: `d086db856be187255b8ec61ef409357393020f32`.
- Detected reachable baseline tag: `3.1.3`.
- Real-repository run exit code: `0`.
- Generated sample: `CHANGELOG.md` in this submission.
- Sample SHA-256: `56B0568737833C89F614AF07D7C62CE9C18BC7AB5C27D26D6918B30CDDB06FBB`.

No API key, network service, or runtime dependency beyond Git and Bash is required to generate a changelog.
