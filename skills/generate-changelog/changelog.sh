#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [--output FILE] [--since TAG] [--repo PATH]
#
# Collects commits since the last git tag (or --since), auto-categorizes
# them into Added / Fixed / Changed / Removed, and writes a
# Keep-a-Changelog style CHANGELOG.md.
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""
REPO="."

usage() {
    cat <<'EOF'
Usage: bash changelog.sh [--output FILE] [--since TAG] [--repo PATH]

  --output FILE   where to write the changelog (default: CHANGELOG.md)
  --since TAG     generate from TAG..HEAD (default: last git tag, or full history)
  --repo PATH     path to the git repo (default: .)
  -h, --help      show this help
EOF
}

# 参数缺值或值像另一个选项时给友好报错（而不是 set -u 的 unbound variable）
need_value() {
    # $1=选项名 $2=值 $3=剩余参数个数
    if [[ "$3" -lt 2 || -z "$2" || "$2" == -* ]]; then
        echo "error: $1 requires a value" >&2
        exit 1
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output) need_value "$1" "${2-}" "$#"; OUTPUT="$2"; shift 2 ;;
        --since)     need_value "$1" "${2-}" "$#"; SINCE="$2";  shift 2 ;;
        --repo)      need_value "$1" "${2-}" "$#"; REPO="$2";   shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "error: unknown argument: $1" >&2; usage; exit 1 ;;
    esac
done

# --output 的相对路径按调用时的目录解析（cd 之前转绝对），符合 CLI 惯例
if [[ "$OUTPUT" != /* ]]; then
    OUTPUT="$PWD/$OUTPUT"
fi

cd "$REPO"
git rev-parse --git-dir >/dev/null 2>&1 || {
    echo "error: '$REPO' is not a git repository" >&2; exit 1
}

if [[ -z "$SINCE" ]]; then
    SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE" ]]; then
    git rev-parse --verify "$SINCE" >/dev/null 2>&1 || {
        echo "error: tag/ref '$SINCE' not found" >&2; exit 1
    }
    RANGE="$SINCE..HEAD"
    RANGE_LABEL="$SINCE → HEAD"
else
    RANGE="HEAD"
    RANGE_LABEL="full history"
fi

# hash|subject, newest first, skip merges
# （不用 mapfile：macOS 自带的 bash 3.2 没有它；while-read 是可移植写法）
COMMITS=()
while IFS= read -r line; do
    COMMITS+=("$line")
done < <(git log "$RANGE" --pretty=tformat:'%h|%s' --no-merges 2>/dev/null || true)

categorize() {
    local subject="$1" lower breaking_re
    lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    # 0. conventional breaking marker (!) 优先级最高，如 feat!: / feat(api)!:
    #    （正则放变量里是 bash [[ =~ ]] 的稳健写法）
    breaking_re='^[a-z]+(\([^)]*\))?!:'
    if [[ "$lower" =~ $breaking_re ]]; then
        printf 'Changed'; return
    fi
    # 1. conventional-commit prefixes win
    case "$lower" in
        feat:*|feature:*)      printf 'Added';   return ;;
        fix:*|bugfix:*|hotfix:*) printf 'Fixed'; return ;;
    esac
    # 2. breaking changes are called out under Changed
    case "$lower" in
        *breaking*|*breaks\ *) printf 'Changed'; return ;;
    esac
    # 3. keyword fallback for free-form subjects
    #    （fix/add 排在 remov 之前："fix broken remove command" 是 fix 不是 Removed）
    case "$lower" in
        *fix*|*bug*|*patch*|*hotfix*|*correct*|*resolv*)
            printf 'Fixed'; return ;;
        *add*|*new*|*introduc*|*implement*|*support*|*creat*|*feat*)
            printf 'Added'; return ;;
        *remov*|*delet*|*drop*|*deprecat*|*"end of life"*)
            printf 'Removed'; return ;;
        *)  printf 'Changed'; return ;;
    esac
}

# 不用关联数组（bash 3.2 不支持 declare -A）：四个分组各一个普通变量
GROUP_ADDED=""
GROUP_FIXED=""
GROUP_CHANGED=""
GROUP_REMOVED=""
for line in "${COMMITS[@]:-}"; do
    hash="${line%%|*}"
    subject="${line#*|}"
    [[ -z "$subject" ]] && continue
    # 跳过文字上的合并噪音（--no-merges 只过滤真合并提交）
    case "$subject" in
        Merge\ branch*|Merge\ pull\ request*|Merge\ remote-tracking\ branch*)
            continue ;;
    esac
    cat="$(categorize "$subject")"
    # 保留 conventional breaking 标记的可视信号
    breaking_mark=""
    breaking_re='^[A-Za-z]+(\([^)]*\))?!:'
    if [[ "$subject" =~ $breaking_re ]]; then
        breaking_mark="⚠️ "
    fi
    # 只剥离已知的 conventional 类型前缀；未知词（如 "important: ..."）保持原样不截断
    clean="$(printf '%s' "$subject" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?(!)?: //')"
    clean="${breaking_mark}${clean}"
    case "$cat" in
        Added)   GROUP_ADDED+="- $clean (${hash})"$'\n' ;;
        Fixed)   GROUP_FIXED+="- $clean (${hash})"$'\n' ;;
        Changed) GROUP_CHANGED+="- $clean (${hash})"$'\n' ;;
        Removed) GROUP_REMOVED+="- $clean (${hash})"$'\n' ;;
    esac
done

# 只打印非空分组
print_group() {
    # $1=标题 $2=内容
    if [[ -n "$2" ]]; then
        echo
        echo "### $1"
        echo
        printf '%s' "$2"
    fi
}

{
    echo "# Changelog"
    echo
    echo "_Generated from git history ($RANGE_LABEL) on $(date -u +%Y-%m-%d)._"
    echo
    if [[ ${#COMMITS[@]} -eq 0 ]]; then
        echo "No changes found ($RANGE_LABEL)."
    else
        echo "## [Unreleased]"
        print_group Added "$GROUP_ADDED"
        print_group Fixed "$GROUP_FIXED"
        print_group Changed "$GROUP_CHANGED"
        print_group Removed "$GROUP_REMOVED"
    fi
} > "$OUTPUT"

echo "wrote $OUTPUT (${#COMMITS[@]} commits from $RANGE_LABEL)"
