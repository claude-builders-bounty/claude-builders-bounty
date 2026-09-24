#!/usr/bin/env bash
# A Git history read failure must never overwrite notes or look like a successful preview.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
generator="$script_dir/../changelog.sh"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT
real_git="$(command -v git)"
export CHANGELOG_TEST_REAL_GIT="$real_git"
mkdir -p "$tmp_root/repo" "$tmp_root/bin"
git -C "$tmp_root/repo" init -q
git -C "$tmp_root/repo" -c user.name=Test -c user.email=test@example.com commit --allow-empty -qm 'feat: example'
cat > "$tmp_root/bin/git" <<'SHIM'
#!/usr/bin/env bash
if [[ "${1:-}" == log ]]; then
  echo 'simulated Git history read failure' >&2
  exit 73
fi
exec "$CHANGELOG_TEST_REAL_GIT" "$@"
SHIM
chmod +x "$tmp_root/bin/git"
printf '%s\n' 'existing release notes' > "$tmp_root/notes.md"
cp "$tmp_root/notes.md" "$tmp_root/expected.md"
for mode in write append preview; do
  args=(--output "$tmp_root/notes.md")
  [[ "$mode" != append ]] || args+=(--append)
  [[ "$mode" != preview ]] || args+=(--preview)
  if PATH="$tmp_root/bin:$PATH" bash "$generator" "$tmp_root/repo" "${args[@]}" > "$tmp_root/stdout" 2> "$tmp_root/stderr"; then
    echo "FAIL: $mode reported success after Git history failure" >&2
    exit 1
  fi
  cmp "$tmp_root/expected.md" "$tmp_root/notes.md"
  test ! -s "$tmp_root/stdout"
  grep -Fq 'simulated Git history read failure' "$tmp_root/stderr"
done
echo 'Git history failure regression passed: write, append, preview'
