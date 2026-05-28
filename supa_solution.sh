# SKILL: Generate a structured CHANGELOG from git history

## changelog.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
SINCE=${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}
OUT=CHANGELOG.md
added=(); fixed=(); changed=(); removed=()
while IFS= read -r msg; do
  case "$msg" in
    feat:*|add:*)    added+=("${msg#*: }") ;;
    fix:*|bug:*)     fixed+=("${msg#*: }") ;;
    remove:*|del:*)  removed+=("${msg#*: }") ;;
    *)               changed+=("${msg#*: }") ;;
  esac
done < <([ -n "$SINCE" ] && git log "${SINCE}..HEAD" --pretty=%s || git log --pretty=%s -50)
{ echo "# CHANGELOG"; echo ""; echo "## [Unreleased] - $(date -I)"; echo ""
  [ ${#added[@]}   -gt 0 ] && { echo "### Added";   printf -- "- %s\n" "${added[@]}";   echo ""; }
  [ ${#fixed[@]}   -gt 0 ] && { echo "### Fixed";   printf -- "- %s\n" "${fixed[@]}";   echo ""; }
  [ ${#changed[@]} -gt 0 ] && { echo "### Changed"; printf -- "- %s\n" "${changed[@]}"; echo ""; }
  [ ${#removed[@]} -gt 0 ] && { echo "### Removed"; printf -- "- %s\n" "${removed[@]}"; }
} > "$OUT"
echo "CHANGELOG.md written ($(wc -l < "$OUT") lines)"
```

## README.md — 3-step install
```markdown
## Setup
1. `curl -sSL https://raw.githubusercontent.com/<your-fork>/main/changelog.sh -o changelog.sh && chmod +x changelog.sh`
2. Run: `./changelog.sh` (auto-detects last git tag; or pass a tag: `./changelog.sh v1.2.0`)
3. Commit: `git add CHANGELOG.md && git commit -m "docs: update changelog"`

## Output example
# CHANGELOG
## [Unreleased] - 2026-05-28
### Added
- user JWT authentication
### Fixed
- memory leak in event loop
### Changed
- refactor database layer
```