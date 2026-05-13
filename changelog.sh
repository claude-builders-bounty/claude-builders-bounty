#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: bash changelog.sh [output_file]

Generate a Markdown CHANGELOG from commits since the latest git tag.
If no tag exists, uses the full commit history.
EOF
  exit 0
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: run inside a git repository." >&2
  exit 1
fi

last_tag=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  last_tag="$(git describe --tags --abbrev=0)"
  range="${last_tag}..HEAD"
else
  range="HEAD"
fi

commits="$(git log --pretty=format:'%s' ${range})"

added=()
fixed=()
changed=()
removed=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  lower="$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ ^(feat|add|new)(\(|:|\s) ]] || [[ "$lower" =~ (add|adds|added) ]]; then
    added+=("$line")
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(|:|\s) ]] || [[ "$lower" =~ (fix|fixed|bug) ]]; then
    fixed+=("$line")
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecate)(\(|:|\s) ]] || [[ "$lower" =~ (remove|removed|delete|deleted|drop|dropped) ]]; then
    removed+=("$line")
  else
    changed+=("$line")
  fi
done <<< "$commits"

{
  echo "# Changelog"
  echo
  echo "## [Unreleased] - $(date -u +%Y-%m-%d)"
  if [[ -n "$last_tag" ]]; then
    echo "_Changes since tag: \`$last_tag\`_"
    echo
  fi

  print_section() {
    local name="$1"; shift
    local -n arr=$1
    if (( ${#arr[@]} > 0 )); then
      echo "### ${name}"
      for item in "${arr[@]}"; do
        echo "- ${item}"
      done
      echo
    fi
  }

  print_section "Added" added
  print_section "Fixed" fixed
  print_section "Changed" changed
  print_section "Removed" removed

  if (( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} == 0 )); then
    echo "- No changes detected in selected range."
  fi
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} from range ${range}"