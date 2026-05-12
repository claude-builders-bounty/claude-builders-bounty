#!/usr/bin/env bash
set -euo pipefail

repo="."
output="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo)
      repo="${2:?Missing value for $1}"
      shift 2
      ;;
    -o|--output)
      output="${2:?Missing value for $1}"
      shift 2
      ;;
    --stdout)
      exec python3 "$(dirname "$0")/scripts/generate_changelog.py" --repo "$repo" --stdout
      ;;
    -h|--help)
      exec python3 "$(dirname "$0")/scripts/generate_changelog.py" --help
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: bash changelog.sh [--repo PATH] [--output CHANGELOG.md] [--stdout]" >&2
      exit 2
      ;;
  esac
done

python3 "$(dirname "$0")/scripts/generate_changelog.py" --repo "$repo" --output "$output"
