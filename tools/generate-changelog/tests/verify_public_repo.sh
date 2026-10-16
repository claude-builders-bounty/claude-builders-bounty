#!/usr/bin/env bash
# Optional online acceptance check. Runs against a real public GitHub repository.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
command -v git >/dev/null || { echo 'Git is required' >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
repo_url=https://github.com/pallets/click.git
printf 'Cloning actual public GitHub repo: %s\n' "$repo_url"
git clone --quiet --filter=blob:none "$repo_url" "$tmp/click"
tag=$(git -C "$tmp/click" describe --tags --abbrev=0 HEAD)
count=$(git -C "$tmp/click" rev-list --count "${tag}..HEAD")
[[ "$count" =~ ^[0-9]+$ ]] || exit 3
if (( count == 0 )); then
  echo 'The public repository has no commits after its latest reachable tag; cannot demonstrate populated sample. Try another repository.' >&2
  exit 3
fi
bash "$here/changelog.sh" --repo "$tmp/click"
sample="$here/examples/CHANGELOG_FROM_PUBLIC_REPO.md"
{
  printf '<!-- Evidence: GitHub public repository %s ; inspected tag %s ; commits since tag %s ; generated UTC %s. -->\n\n' "$repo_url" "$tag" "$count" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat "$tmp/click/CHANGELOG.md"
} > "$sample"
[[ -s "$sample" ]] || exit 4
grep -q '^### Added' "$sample"
grep -q '^### Fixed' "$sample"
grep -q '^### Changed' "$sample"
grep -q '^### Removed' "$sample"
printf 'PUBLIC REPO TEST PASSED: %s ; tag=%s ; commits=%s\nSample: %s\n' "$repo_url" "$tag" "$count" "$sample"
