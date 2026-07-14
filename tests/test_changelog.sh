#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

git -C "${tmp_dir}" init -q
git -C "${tmp_dir}" config user.email "test@example.com"
git -C "${tmp_dir}" config user.name "Test User"

printf 'one\n' >"${tmp_dir}/file.txt"
git -C "${tmp_dir}" add file.txt
git -C "${tmp_dir}" commit -q -m "feat: initial feature"
git -C "${tmp_dir}" tag v1.0.0

printf 'two\n' >>"${tmp_dir}/file.txt"
git -C "${tmp_dir}" add file.txt
git -C "${tmp_dir}" commit -q -m "fix: repair edge case"

printf 'three\n' >>"${tmp_dir}/file.txt"
git -C "${tmp_dir}" add file.txt
git -C "${tmp_dir}" commit -q -m "docs: update usage"

rm "${tmp_dir}/file.txt"
git -C "${tmp_dir}" add file.txt
git -C "${tmp_dir}" commit -q -m "remove: old fixture"

output_file="${tmp_dir}/CHANGELOG.md"
bash "${root_dir}/changelog.sh" "${tmp_dir}" "${output_file}" >/dev/null

grep -q "## Unreleased" "${output_file}"
grep -q "_Range: v1.0.0..HEAD_" "${output_file}"
grep -q "### Fixed" "${output_file}"
grep -q "fix: repair edge case" "${output_file}"
grep -q "### Changed" "${output_file}"
grep -q "docs: update usage" "${output_file}"
grep -q "### Removed" "${output_file}"
grep -q "remove: old fixture" "${output_file}"

if grep -q "feat: initial feature" "${output_file}"; then
  echo "tagged commit should not appear in generated changelog" >&2
  exit 1
fi

echo "changelog test passed"

no_tag_repo="${tmp_dir}/no-tag"
mkdir "${no_tag_repo}"
git -C "${no_tag_repo}" init -q
git -C "${no_tag_repo}" config user.email "test@example.com"
git -C "${no_tag_repo}" config user.name "Test User"

printf 'one\n' >"${no_tag_repo}/file.txt"
git -C "${no_tag_repo}" add file.txt
git -C "${no_tag_repo}" commit -q -m "feat: no tag feature"

no_tag_output="${tmp_dir}/NO_TAG_CHANGELOG.md"
bash "${root_dir}/changelog.sh" "${no_tag_repo}" "${no_tag_output}" >/dev/null

grep -q "_Range: all history_" "${no_tag_output}"
grep -q "feat: no tag feature" "${no_tag_output}"

echo "no-tag changelog test passed"
