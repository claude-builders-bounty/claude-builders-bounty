#!/usr/bin/env bash
#
# 便携自检：创建临时 git 仓库，制造 Added/Fixed/Changed/Removed 各一类提交，
# 运行 changelog.sh，断言四类都正确归类。退出码 0 表示通过。
#
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../changelog.sh"

if [[ ! -f "$SCRIPT" ]]; then
  echo "找不到 changelog.sh（$SCRIPT）" >&2
  exit 1
fi

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cd "$TMP"
git init -q
git config user.email "test@local"
git config user.name  "Test"
echo init > init.txt; git add init.txt; git commit -qm "chore: initial commit"
git tag v0.1.0
# 四类提交（中英文混合）
echo a > feat.txt;  git add feat.txt;  git commit -qm "feat: 新增 CSV 批量清洗"
echo b > fix.txt;   git add fix.txt;   git commit -qm "fix: 修复引号解析错误"
echo c > ref.txt;   git add ref.txt;   git commit -qm "refactor: 重构计费逻辑"
echo d > rm.txt;    git add rm.txt;    git commit -qm "remove: 删除旧模板"
echo e > zh.txt;    git add zh.txt;    git commit -qm "新增 导出 Markdown 功能"
echo f > zhf.txt;   git add zhf.txt;   git commit -qm "修复 登录态过期导致的 403"

OUT="$TMP/CHANGELOG.md"
bash "$SCRIPT" --repo "$TMP" --output "$OUT" >/dev/null
rc=$?
if [[ $rc -ne 0 || ! -f "$OUT" ]]; then
  echo "FAIL: 脚本未正常生成 CHANGELOG.md (rc=$rc)"; exit 1
fi

fail=0
assert_has() {
  local label="$1" pattern="$2"
  if grep -q "$pattern" "$OUT"; then
    echo "PASS: $label"
  else
    echo "FAIL: $label（未在输出中找到 '$pattern'）"; fail=1
  fi
}

assert_has "Added 含 feat"     "^- feat: 新增 CSV 批量清洗 ("
assert_has "Added 含中文新增"  "^- 新增 导出 Markdown 功能 ("
assert_has "Fixed 含 fix"      "^- fix: 修复引号解析错误 ("
assert_has "Fixed 含中文修复"  "^- 修复 登录态过期导致的 403 ("
assert_has "Changed 含 refactor" "^- refactor: 重构计费逻辑 ("
assert_has "Removed 含 remove" "^- remove: 删除旧模板 ("
assert_has "范围自 tag 起"      "自 tag \`v0.1.0\`"
assert_has "四类标题齐全"       "### Added"
grep -q "### Fixed"   "$OUT" && grep -q "### Changed" "$OUT" && grep -q "### Removed" "$OUT" \
  && echo "PASS: ### Fixed / Changed / Removed 均存在" || { echo "FAIL: 分类标题缺失"; fail=1; }

if [[ $fail -eq 0 ]]; then
  echo; echo "✅ 全部通过"
  exit 0
else
  echo; echo "❌ 存在失败项"; exit 1
fi
