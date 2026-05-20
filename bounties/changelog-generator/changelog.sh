#!/usr/bin/env bash
set -euo pipefail

repo="."
output="CHANGELOG.md"
version="Unreleased"

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo PATH] [--output FILE] [--version NAME]

Generate a structured CHANGELOG.md from git history since the latest tag.

Options:
  --repo PATH      Git repository to inspect. Defaults to current directory.
  --output FILE    Output file path, relative to the repo unless absolute. Defaults to CHANGELOG.md.
  --version NAME   Changelog section name. Defaults to Unreleased.
  -h, --help       Show this help message.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?--repo requires a path}"
      shift 2
      ;;
    --output)
      output="${2:?--output requires a file path}"
      shift 2
      ;;
    --version)
      version="${2:?--version requires a name}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

git_in_repo() {
  git -C "$repo" "$@"
}

if ! git_in_repo rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $repo is not a git repository" >&2
  exit 1
fi

repo_root="$(git_in_repo rev-parse --show-toplevel)"
if [[ "$output" = /* ]]; then
  output_path="$output"
else
  output_path="$repo_root/$output"
fi

latest_tag=""
if latest_tag="$(git_in_repo describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
else
  range="HEAD"
fi

remote_url="$(git_in_repo config --get remote.origin.url || true)"
repo_web_url=""
if [[ "$remote_url" =~ ^git@github.com:(.+)\.git$ ]]; then
  repo_web_url="https://github.com/${BASH_REMATCH[1]}"
elif [[ "$remote_url" =~ ^https://github.com/(.+)\.git$ ]]; then
  repo_web_url="https://github.com/${BASH_REMATCH[1]}"
elif [[ "$remote_url" =~ ^https://github.com/(.+)$ ]]; then
  repo_web_url="https://github.com/${BASH_REMATCH[1]}"
fi

today="$(date +%Y-%m-%d)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
touch "$added" "$fixed" "$changed" "$removed"

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*): }"
  subject="${subject#*:}"
  subject="${subject#*)}"
  subject="${subject#"${subject%%[![:space:]]*}"}"
  subject="${subject%"${subject##*[![:space:]]}"}"
  if [[ -z "$subject" ]]; then
    subject="$1"
  fi
  printf '%s' "$subject"
}

category_for() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  local prefix="${subject%%:*}"
  local prefix_base="${prefix%%(*}"

  if [[ "$prefix_base" == "feat" || "$prefix_base" == "feature" ]] || [[ "$subject" =~ (^|[^[:alnum:]_])(add|adds|added|create|creates|created|implement|implements|implemented|introduce|introduces|introduced)([^[:alnum:]_]|$) ]]; then
    printf 'Added'
  elif [[ "$prefix_base" == "fix" ]] || [[ "$subject" =~ (^|[^[:alnum:]_])(fix|fixes|fixed|bug|bugs|resolve|resolves|resolved|patch|patched)([^[:alnum:]_]|$) ]]; then
    printf 'Fixed'
  elif [[ "$prefix_base" == "remove" || "$prefix_base" == "removed" ]] || [[ "$subject" =~ (^|[^[:alnum:]_])(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecates|deprecated)([^[:alnum:]_]|$) ]]; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

append_entry() {
  local category="$1"
  local hash="$2"
  local subject="$3"
  local short_hash="${hash:0:7}"
  local message
  local target

  message="$(clean_subject "$subject")"
  if [[ -n "$repo_web_url" ]]; then
    message="- ${message} ([${short_hash}](${repo_web_url}/commit/${hash}))"
  else
    message="- ${message} (${short_hash})"
  fi

  case "$category" in
    Added) target="$added" ;;
    Fixed) target="$fixed" ;;
    Removed) target="$removed" ;;
    *) target="$changed" ;;
  esac
  printf '%s\n' "$message" >> "$target"
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  category="$(category_for "$subject")"
  append_entry "$category" "$hash" "$subject"
done < <(git_in_repo log "$range" --no-merges --pretty=format:'%H%x09%s')

new_section="$tmp_dir/new-section.md"
{
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "$version" "$today"
  if [[ -n "$latest_tag" ]]; then
    printf 'Commits since `%s`.\n\n' "$latest_tag"
  else
    printf 'Commits from the full git history because no tags were found.\n\n'
  fi

  wrote_any=0
  for section in Added Fixed Changed Removed; do
    file_var="$(printf '%s' "$section" | tr '[:upper:]' '[:lower:]')"
    file_path="${!file_var}"
    if [[ -s "$file_path" ]]; then
      printf '### %s\n\n' "$section"
      cat "$file_path"
      printf '\n'
      wrote_any=1
    fi
  done

  if [[ "$wrote_any" -eq 0 ]]; then
    printf 'No commits found since the latest tag.\n\n'
  fi
} > "$new_section"

if [[ -f "$output_path" ]]; then
  existing_body="$tmp_dir/existing-body.md"
  awk 'NR == 1 && $0 == "# Changelog" {next} {print}' "$output_path" > "$existing_body"
  cat "$new_section" "$existing_body" > "$output_path"
else
  mkdir -p "$(dirname "$output_path")"
  cp "$new_section" "$output_path"
fi

echo "Wrote $output_path"
