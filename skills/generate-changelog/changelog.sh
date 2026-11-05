#!/usr/bin/env bash
#
# changelog.sh — 零依赖 CHANGELOG 生成器（bash + git）
# ---------------------------------------------------------------
# 从 git 历史（自上一个 tag 起）自动生成结构化的 CHANGELOG.md，
# 按 Conventional Commits 前缀 / 中文关键词将提交归类为
#   Added / Fixed / Changed / Removed
#
# 兼容 macOS bash 3.2 与 Linux bash 4+（不使用 mapfile / nameref / ${var,,}）。
#
# 用法：
#   bash changelog.sh [--repo PATH] [--output FILE] [--version VER]
#                     [--since-tag TAG] [--dry-run] [-h|--help]
# 也可被 SKILL.md 包装，在 Claude Code 中以 /generate-changelog 调用。
#
# 兼容性说明：macOS 默认 bash 为 3.2，空数组在 set -u 下会报
# "unbound variable"，且 ((0)) 在 set -e 下会误触发退出。
# 故不使用 set -e/-u；错误（非 git 仓库、git log 失败）已显式处理。
set -o pipefail

REPO="."
OUTPUT="CHANGELOG.md"
VERSION=""
SINCE_TAG=""
DRY_RUN=0

usage() {
  sed -n '2,20p' "$0" | sed 's/^#\{1,2\} //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo|-r)      REPO="$2"; shift 2;;
    --output|-o)    OUTPUT="$2"; shift 2;;
    --version|-v)   VERSION="$2"; shift 2;;
    --since-tag)    SINCE_TAG="$2"; shift 2;;
    --dry-run)      DRY_RUN=1; shift;;
    -h|--help)      usage 0;;
    *) echo "未知参数: $1" >&2; usage 1;;
  esac
done

# 校验 git 仓库
if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "错误：'$REPO' 不是 git 仓库" >&2
  exit 1
fi

# 取上一个 tag（未指定时）
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_NOTE="自 tag \`${SINCE_TAG}\` 之后的提交"
else
  RANGE="HEAD"
  RANGE_NOTE="仓库全部提交（未检测到 tag，使用完整历史）"
fi

# 读取提交：<哈希><TAB><主题>
git_out=$(git -C "$REPO" log "$RANGE" --no-merges --pretty=format:'%H%x09%s' 2>/dev/null) \
  || { echo "读取 git log 失败（$RANGE）" >&2; exit 1; }

# 分类函数：返回 Added / Fixed / Changed / Removed
classify() {
  local subj="$1" low t
  low=$(printf '%s' "$subj" | tr '[:upper:]' '[:lower:]')
  # 统一中英文冒号为 ASCII 冒号，避免正则内多字节字符问题
  norm=$(printf '%s' "$low" | sed 's/：/:/g')
  # 1) Conventional Commits 前缀：type(scope): msg
  # 注意：bash 3.2 直接把正则字面量写在 [[ =~ ]] 内会解析失败，
  #       必须存入变量后以未加引号的形式引用（已在 macOS 3.2 验证）。
  conv_re='^([a-z]+)(\([^)]*\))?!?[:][[:space:]]*(.*)$'
  if [[ "$norm" =~ $conv_re ]]; then
    t="${BASH_REMATCH[1]}"
    case "$t" in
      feat|feature|add)        echo Added;   return;;
      fix|bug|hotfix)          echo Fixed;   return;;
      remove|rm|delete)        echo Removed; return;;
      refactor|perf|style|chore|build|ci|improve|update|change|docs|rename)
                              echo Changed; return;;
    esac
  fi
  # 2) 中英文关键词
  case "$low" in
    *新增*|*添加*|*增加*|*新功能*|*支持*|*feat*|*"add "*|*add:*)
      echo Added; return;;
  esac
  case "$low" in
    *修复*|*修正*|*解决*|*修补*|*fix*|*bug*)
      echo Fixed; return;;
  esac
  case "$low" in
    *删除*|*移除*|*去掉*|*remove*|*delete*|*"rm "*)
      echo Removed; return;;
  esac
  case "$low" in
    *重构*|*优化*|*改进*|*升级*|*更新*|*调整*|*修改*|*refactor*|*perf*|\
*update*|*change*|*improve*|*chore*|*rename*)
      echo Changed; return;;
  esac
  # 3) 兜底：归入 Changed（避免丢失提交）
  echo Changed
}

ADDED=(); FIXED=(); CHANGED=(); REMOVED=()
count=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  sha="${line%%$'\t'*}"
  subj="${line#*$'\t'}"
  short="${sha:0:7}"
  grp=$(classify "$subj")
  entry="- ${subj} (${short})"
  case "$grp" in
    Added)   ADDED+=("$entry");;
    Fixed)   FIXED+=("$entry");;
    Removed) REMOVED+=("$entry");;
    *)       CHANGED+=("$entry");;
  esac
  count=$((count+1))
done <<< "$git_out"

TODAY=$(date +%Y-%m-%d)
VER="${VERSION:-Unreleased}"

render_section() {
  local title="$1"; shift
  if [[ $# -gt 0 ]]; then
    echo "### $title"
    printf '%s\n' "$@"
    echo
  fi
}

OUT=$(
  {
    echo "# Changelog"
    echo
    echo "本文件由 \`changelog.sh\` 依据 git 历史自动生成，分类遵循 Conventional Commits 与中文关键词识别。"
    echo
    echo "## [${VER}] - ${TODAY}"
    echo
    echo "${RANGE_NOTE}（共 ${count} 条提交）。"
    echo
    ((${#ADDED[@]}))   && render_section "Added"   "${ADDED[@]}"
    ((${#FIXED[@]}))   && render_section "Fixed"   "${FIXED[@]}"
    ((${#CHANGED[@]})) && render_section "Changed" "${CHANGED[@]}"
    ((${#REMOVED[@]})) && render_section "Removed" "${REMOVED[@]}"
  }
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' "$OUT"
else
  printf '%s\n' "$OUT" > "$OUTPUT"
  echo "已生成 $OUTPUT（${count} 条提交 · Added=$((${#ADDED[@]})) Fixed=$((${#FIXED[@]})) Changed=$((${#CHANGED[@]})) Removed=$((${#REMOVED[@]}))）"
fi
