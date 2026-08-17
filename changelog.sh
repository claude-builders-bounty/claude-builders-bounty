#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run inside a Git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  heading="Changes since ${latest_tag}"
else
  range="HEAD"
  heading="Changes from repository history"
fi

mapfile -t commits < <(
  git log "$range" --no-merges --pretty=format:'%s' 2>/dev/null || true
)

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

for message in "${commits[@]}"; do
  lower="$(printf '%s' "$message" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' introduce '*|*' create '*)
      added+=("$message")
      ;;
    fix:*|fixed:*|bugfix:*|*' fix '*|*' bug '*|*' repair '*)
      fixed+=("$message")
      ;;
    remove:*|removed:*|delete:*|deleted:*|*' remove '*|*' delete '*|*' deprecat '*)
      removed+=("$message")
      ;;
    *)
      changed+=("$message")
      ;;
  esac
done

write_section() {
  title="$1"
  shift
  entries=("$@")

  {
    echo "## ${title}"
    echo

    if [[ ${#entries[@]} -eq 0 ]]; then
      echo "- No changes."
    else
      for entry in "${entries[@]}"; do
        printf -- '- %s\n' "$entry"
      done
    fi

    echo
  } >> "$OUTPUT"
}

{
  echo "# Changelog"
  echo
  echo "$heading"
  echo
} > "$OUTPUT"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Generated ${OUTPUT}"