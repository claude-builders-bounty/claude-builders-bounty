#!/usr/bin/env bash
# Real-public-repository acceptance demonstration; no writes to upstream.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
TARGET="https://github.com/pallets/itsdangerous.git"
echo "Repository: $TARGET"
git clone --quiet "$TARGET" "$WORK/repo"
git -C "$WORK/repo" fetch --tags --quiet
echo "Resolved HEAD: $(git -C "$WORK/repo" rev-parse HEAD)"
echo "Nearest reachable tag: $(git -C "$WORK/repo" describe --tags --abbrev=0 HEAD 2>/dev/null || echo '(none)')"
python3 "$ROOT/changelog.py" --repo "$WORK/repo" --output "$WORK/CHANGELOG.md"
test -s "$WORK/CHANGELOG.md"
grep -q '^# Changelog' "$WORK/CHANGELOG.md"
grep -q '^## \[Unreleased\]' "$WORK/CHANGELOG.md"
echo '=== Real repo generated changelog ==='
cat "$WORK/CHANGELOG.md"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  echo '## Real-repository changelog demonstration' >> "$GITHUB_STEP_SUMMARY"
  echo "Source: $TARGET" >> "$GITHUB_STEP_SUMMARY"
  echo "HEAD: $(git -C "$WORK/repo" rev-parse HEAD)" >> "$GITHUB_STEP_SUMMARY"
  echo '' >> "$GITHUB_STEP_SUMMARY"
  echo '\`\`\`markdown' >> "$GITHUB_STEP_SUMMARY"
  cat "$WORK/CHANGELOG.md" >> "$GITHUB_STEP_SUMMARY"
  echo '\`\`\`' >> "$GITHUB_STEP_SUMMARY"
fi
if [[ -n "${DEMO_OUTPUT_DIR:-}" ]]; then
  mkdir -p "$DEMO_OUTPUT_DIR"
  cp "$WORK/CHANGELOG.md" "$DEMO_OUTPUT_DIR/CHANGELOG.real-repo.md"
  { echo "repository=$TARGET"; echo "head=$(git -C "$WORK/repo" rev-parse HEAD)"; git -C "$WORK/repo" describe --tags --abbrev=0 HEAD 2>/dev/null | sed 's/^/nearest_tag=/'; } > "$DEMO_OUTPUT_DIR/provenance.txt"
fi
