#!/bin/bash
# =============================================================================
# CHANGELOG Generator - 自动生成结构化CHANGELOG
# 赏金任务: $50 - Generate a structured CHANGELOG from git history
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"
OUTPUT_FILE="${REPO_ROOT}/CHANGELOG.md"

# 获取上一个tag
get_last_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo ""
}

# 获取提交范围
get_commit_range() {
    local last_tag=$(get_last_tag)
    if [ -z "$last_tag" ]; then
        echo "HEAD"
    else
        echo "${last_tag}..HEAD"
    fi
}

# 分类提交
categorize_commit() {
    local message="$1"
    local category="Other"
    
    # 转换为小写进行匹配
    local lower_msg=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower_msg" | grep -qE "(add|feature|feat|new|implement|introduce)"; then
        category="Added"
    elif echo "$lower_msg" | grep -qE "(fix|bug|repair|correct|resolve|patch)"; then
        category="Fixed"
    elif echo "$lower_msg" | grep -qE "(change|update|modify|refactor|improve|enhance|optimize)"; then
        category="Changed"
    elif echo "$lower_msg" | grep -qE "(remove|delete|drop|clean|cleanup|deprecate)"; then
        category="Removed"
    fi
    
    echo "$category"
}

# 生成CHANGELOG
generate_changelog() {
    local commit_range=$(get_commit_range)
    local last_tag=$(get_last_tag)
    local version=""
    local date_str=$(date +%Y-%m-%d)
    
    # 确定版本号
    if [ -z "$last_tag" ]; then
        version="Unreleased"
    else
        version="Unreleased"
    fi
    
    echo -e "${BLUE}🔍 扫描提交范围: ${commit_range}${NC}"
    
    # 临时存储各类提交
    local added_commits=()
    local fixed_commits=()
    local changed_commits=()
    local removed_commits=()
    local other_commits=()
    
    # 读取提交
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        
        local hash=$(echo "$line" | cut -d' ' -f1)
        local message=$(echo "$line" | cut -d' ' -f2-)
        local category=$(categorize_commit "$message")
        local formatted="- ${message} (${hash:0:7})"
        
        case "$category" in
            "Added") added_commits+=("$formatted") ;;
            "Fixed") fixed_commits+=("$formatted") ;;
            "Changed") changed_commits+=("$formatted") ;;
            "Removed") removed_commits+=("$formatted") ;;
            *) other_commits+=("$formatted") ;;
        esac
    done < <(git log "$commit_range" --pretty=format:"%h %s" --no-merges 2>/dev/null || echo "")
    
    # 生成输出
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo ""
        echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
        echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
        echo ""
        echo "## [${version}] - ${date_str}"
        echo ""
        
        if [ ${#added_commits[@]} -gt 0 ]; then
            echo "### Added"
            for commit in "${added_commits[@]}"; do
                echo "$commit"
            done
            echo ""
        fi
        
        if [ ${#changed_commits[@]} -gt 0 ]; then
            echo "### Changed"
            for commit in "${changed_commits[@]}"; do
                echo "$commit"
            done
            echo ""
        fi
        
        if [ ${#fixed_commits[@]} -gt 0 ]; then
            echo "### Fixed"
            for commit in "${fixed_commits[@]}"; do
                echo "$commit"
            done
            echo ""
        fi
        
        if [ ${#removed_commits[@]} -gt 0 ]; then
            echo "### Removed"
            for commit in "${removed_commits[@]}"; do
                echo "$commit"
            done
            echo ""
        fi
        
        if [ ${#other_commits[@]} -gt 0 ]; then
            echo "### Other"
            for commit in "${other_commits[@]}"; do
                echo "$commit"
            done
            echo ""
        fi
        
    } > "$OUTPUT_FILE"
    
    local total=$(( ${#added_commits[@]} + ${#fixed_commits[@]} + ${#changed_commits[@]} + ${#removed_commits[@]} + ${#other_commits[@]} ))
    
    echo -e "${GREEN}✅ CHANGELOG生成完成!${NC}"
    echo -e "${GREEN}   文件: ${OUTPUT_FILE}${NC}"
    echo -e "${GREEN}   提交数: ${total}${NC}"
    echo ""
    echo -e "${YELLOW}分类统计:${NC}"
    echo "  Added:   ${#added_commits[@]}"
    echo "  Changed: ${#changed_commits[@]}"
    echo "  Fixed:   ${#fixed_commits[@]}"
    echo "  Removed: ${#removed_commits[@]}"
    echo "  Other:   ${#other_commits[@]}"
}

# 显示帮助
show_help() {
    echo "CHANGELOG Generator - 自动生成结构化CHANGELOG"
    echo ""
    echo "用法:"
    echo "  ./changelog.sh           生成CHANGELOG.md"
    echo "  ./changelog.sh --help    显示帮助"
    echo ""
    echo "功能:"
    echo "  - 自动获取上次tag以来的所有提交"
    echo "  - 智能分类: Added/Fixed/Changed/Removed"
    echo "  - 输出标准格式的CHANGELOG.md"
    echo ""
    echo "分类规则:"
    echo "  Added   - 包含 add/feature/feat/new/implement"
    echo "  Fixed   - 包含 fix/bug/repair/correct/resolve"
    echo "  Changed - 包含 change/update/modify/refactor/improve"
    echo "  Removed - 包含 remove/delete/drop/clean/deprecate"
}

# 主逻辑
main() {
    # 检查是否在git仓库
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}❌ 错误: 当前目录不是git仓库${NC}"
        exit 1
    fi
    
    # 检查参数
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
    esac
    
    echo -e "${BLUE}🚀 开始生成CHANGELOG...${NC}"
    echo ""
    
    generate_changelog
    
    echo ""
    echo -e "${GREEN}🎉 完成! 查看文件: ${OUTPUT_FILE}${NC}"
}

main "$@"
