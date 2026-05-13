#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from a project's git history.
# Usage: bash changelog.sh [--repo /path/to/repo] [--since v1.0.0]
#
# Categorizes commits into:
#   - Added    (new features, capabilities)
#   - Fixed    (bug fixes, corrections)
#   - Changed  (updates, refactors, improvements)
#   - Removed  (deleted, deprecated, cleaned)

set -euo pipefail

# Detect python command
PYTHON="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON="python"
fi

# Run the Python script from the same directory as this bash script
"$PYTHON" generate_changelog.py "$@"
