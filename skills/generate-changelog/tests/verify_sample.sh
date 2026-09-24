#!/usr/bin/env bash
# Reproduce the committed sample against its source history, using the current generator.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"
sample_path='skills/generate-changelog/samples/CHANGELOG.sample.md'
sample_commit="$(git -C "$repo_root" log -1 --format=%H -- "$sample_path")"
source_commit="$(git -C "$repo_root" rev-parse "${sample_commit}^")"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT
git clone -q --shared --no-checkout "$repo_root" "$tmp_root/repo"
git -C "$tmp_root/repo" checkout -q --detach "$source_commit"
bash "$script_dir/../changelog.sh" "$tmp_root/repo" --preview > "$tmp_root/preview" 2> "$tmp_root/stderr"
grep -v '^## \[.*\] - ' "$tmp_root/preview" > "$tmp_root/actual"
grep -v '^## \[.*\] - ' "$repo_root/$sample_path" > "$tmp_root/expected"
diff -u "$tmp_root/expected" "$tmp_root/actual"
echo "Sample verification passed at source $source_commit"
