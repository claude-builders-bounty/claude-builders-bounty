#!/usr/bin/env bash
set -euo pipefail

REPO="."
OUTPUT="CHANGELOG.md"

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo PATH] [--output FILE]

Generate a structured CHANGELOG.md from git commits since the latest tag.

Options:
  --repo PATH       Git repository to inspect. Defaults to the current directory.
  --output FILE     Output file. Relative paths are written inside --repo.
  -h, --help        Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO="${2:?Missing value for --repo}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:?Missing value for --output}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi

REPO_ROOT="$(git -C "$REPO" rev-parse --show-toplevel)"
case "$OUTPUT" in
  /*) OUTPUT_PATH="$OUTPUT" ;;
  *) OUTPUT_PATH="$REPO_ROOT/$OUTPUT" ;;
esac

LAST_TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_NOTE="Generated from commits after \`$LAST_TAG\`."
else
  RANGE="HEAD"
  RANGE_NOTE="No git tags found; generated from all reachable commits."
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

categorize_subject() {
  subject="$1"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if printf '%s' "$lower" | grep -Eq '^(feat|feature|add|added)(\([^)]+\))?!?:'; then
    echo "Added"
    return
  elif printf '%s' "$lower" | grep -Eq '^(fix|bug|bugfix|repair|patch)(\([^)]+\))?!?:'; then
    echo "Fixed"
    return
  elif printf '%s' "$lower" | grep -Eq '^(remove|removed|delete|deleted|drop|dropped)(\([^)]+\))?!?:'; then
    echo "Removed"
    return
  fi

  if printf '%s' "$lower" | grep -Eq '(^|[^a-z])(add|adds|added|create|creates|created|implement|implements|implemented|introduce|introduces|introduced)([^a-z]|$)'; then
    echo "Added"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(fix|fixes|fixed|bug|repair|repairs|repaired|resolve|resolves|resolved)([^a-z]|$)'; then
    echo "Fixed"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped)([^a-z]|$)'; then
    echo "Removed"
  else
    echo "Changed"
  fi
}

clean_subject() {
  printf '%s' "$1" \
    | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
    | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//' \
    | sed -E 's/^[[:space:]]+//'
}

COMMITS_FILE="$TMPDIR/commits"
git -C "$REPO_ROOT" log --no-merges --pretty=format:'%h%x1f%s' "$RANGE" > "$COMMITS_FILE"

while IFS="$(printf '\037')" read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "${hash:-}" ] || continue
  category="$(categorize_subject "$subject")"
  summary="$(clean_subject "$subject")"
  [ -n "$summary" ] || summary="$subject"
  printf -- '- %s (`%s`)\n' "$summary" "$hash" >> "$TMPDIR/$category"
done < "$COMMITS_FILE"

TODAY="$(date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "## Unreleased - $TODAY"
  echo
  echo "_${RANGE_NOTE}_"
  echo
  for category in Added Fixed Changed Removed; do
    echo "### $category"
    echo
    if [ -s "$TMPDIR/$category" ]; then
      cat "$TMPDIR/$category"
    else
      echo "- No changes."
    fi
    echo
  done
} > "$OUTPUT_PATH"

echo "Wrote $OUTPUT_PATH"
