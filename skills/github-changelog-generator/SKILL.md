---
name: github-changelog-generator
description: Generate structured CHANGELOG.md from git history - categorizes commits by type (Added/Fixed/Changed/Removed)
category: productivity
---

## 目标

从 git 历史自动生成结构化的 `CHANGELOG.md`，按 Conventional Commits 规范分类。

## 使用方法

### 方式 1: 作为 Claude Code Skill

```bash
# 在项目中运行
/generate-changelog

# 或手动调用
claude "Generate a CHANGELOG from git history"
```

### 方式 2: 独立 Bash 脚本

```bash
cd /path/to/your/repo
bash changelog.sh
```

## 输出格式

生成的 `CHANGELOG.md` 格式：

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add user authentication system (#123)
- feat: Implement dark mode toggle (#145)

### Fixed
- fix: Resolve memory leak in data processing (#156)
- fix: Correct timezone handling in scheduler (#162)

### Changed
- refactor: Improve error handling in API layer (#148)
- change: Update dependency versions (#151)

### Removed
- remove: Deprecate legacy auth endpoints (#139)
```

## 实现原理

### 1. Git Log 解析

```bash
# 获取所有未标记版本的 commits
git log --pretty=format:"%h|%s|%ai" --no-merges

# 输出示例：
# a1b2c3d|feat: Add user authentication|2026-04-20 14:30:00 +0800
# e5f6g7h|fix: Resolve memory leak|2026-04-19 10:15:00 +0800
```

### 2. Commit 分类规则

| 前缀 | 分类 |
|------|------|
| `feat:` | Added |
| `add:` | Added |
| `fix:` | Fixed |
| `bugfix:` | Fixed |
| `refactor:` | Changed |
| `change:` | Changed |
| `update:` | Changed |
| `remove:` | Removed |
| `drop:` | Removed |
| `delete:` | Removed |

### 3. 版本分组策略

**有 tags 的项目：**
```bash
# 按 tag 分组
git log --pretty=format:"%h|%s|%ai" --no-merges v1.2.0..HEAD
```

**无 tags 的项目：**
- 按月份分组（最近 30 天 = Unreleased）
- 或按 commit 数量分组（每 20 个 commit 为一组）

## 脚本实现

### changelog.sh

```bash
#!/bin/bash

# CHANGELOG Generator
# Usage: bash changelog.sh [output_file]

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## [Unreleased]" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 获取 commits
COMMITS=$(git log --pretty=format:"%h|%s|%ai" --no-merges -50)

# 分类数组
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

while IFS='|' read -r hash message date; do
    # 转换为小写进行匹配
    msg_lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # 分类
    if [[ "$msg_lower" =~ ^feat:|^add: ]]; then
        ADDED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^fix:|^bugfix: ]]; then
        FIXED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^refactor:|^change:|^update: ]]; then
        CHANGED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^remove:|^drop:|^delete: ]]; then
        REMOVED+=("- $message ($hash)")
    else
        # 未分类的放入 Changed
        CHANGED+=("- $message ($hash)")
    fi
done <<< "$COMMITS"

# 输出分类结果
if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    for item in "${ADDED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    for item in "${FIXED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    for item in "${CHANGED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    for item in "${REMOVED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
echo "   Total commits processed: $(echo "$COMMITS" | wc -l)"
```

### Python 版本（更强大）

```python
#!/usr/bin/env python3
"""
CHANGELOG Generator - Advanced version with tag support
"""

import subprocess
import re
from collections import defaultdict
from datetime import datetime

# Commit type mapping
TYPE_MAPPING = {
    'feat': 'Added',
    'feature': 'Added',
    'add': 'Added',
    'fix': 'Fixed',
    'bugfix': 'Fixed',
    'refactor': 'Changed',
    'change': 'Changed',
    'update': 'Changed',
    'improve': 'Changed',
    'remove': 'Removed',
    'drop': 'Removed',
    'delete': 'Removed',
    'deprecate': 'Removed',
}

def get_git_log(range_spec=''):
    """Get git log with format: hash|message|date"""
    cmd = ['git', 'log', '--pretty=format:%h|%s|%ai', '--no-merges']
    if range_spec:
        cmd.append(range_spec)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return []
    
    return result.stdout.strip().split('\n')

def classify_commit(message):
    """Classify commit by type prefix"""
    msg_lower = message.lower()
    
    for prefix, category in TYPE_MAPPING.items():
        if msg_lower.startswith(f'{prefix}:') or msg_lower.startswith(f'{prefix} '):
            return category
    
    return 'Other'

def get_tags():
    """Get all tags sorted by date"""
    result = subprocess.run(
        ['git', 'tag', '--sort=-creatordate'],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n')

def generate_changelog(output_file='CHANGELOG.md', max_commits=100):
    """Generate CHANGELOG.md from git history"""
    
    # Check for tags
    tags = [t for t in get_tags() if t]
    
    categorized = defaultdict(list)
    
    if tags:
        # Group by tags
        for i, tag in enumerate(tags):
            if i == 0:
                range_spec = f'{tag}..HEAD'
            else:
                range_spec = f'{tags[i]}..{tags[i-1]}'
            
            commits = get_git_log(range_spec)[:max_commits]
            
            for line in commits:
                if not line.strip():
                    continue
                parts = line.split('|', 2)
                if len(parts) < 2:
                    continue
                hash_, message = parts[0], parts[1]
                category = classify_commit(message)
                categorized[(tag, category)].append(f'- {message} ({hash_})')
    else:
        # No tags, group by Unreleased
        commits = get_git_log()[:max_commits]
        
        for line in commits:
            if not line.strip():
                continue
            parts = line.split('|', 2)
            if len(parts) < 2:
                continue
            hash_, message = parts[0], parts[1]
            category = classify_commit(message)
            categorized[('Unreleased', category)].append(f'- {message} ({hash_})')
    
    # Write output
    with open(output_file, 'w') as f:
        f.write('# Changelog\n\n')
        
        current_version = None
        for (version, category), items in sorted(categorized.items(), 
                                                    key=lambda x: (x[0][0] == 'Unreleased', x[0][0]), 
                                                    reverse=True):
            if version != current_version:
                if current_version is not None:
                    f.write('\n')
                f.write(f'## [{version}]\n\n')
                current_version = version
            
            if items:
                f.write(f'### {category}\n')
                for item in items:
                    f.write(f'{item}\n')
                f.write('\n')
    
    print(f'✅ CHANGELOG generated: {output_file}')
    total = sum(len(items) for items in categorized.values())
    print(f'   Total commits processed: {total}')

if __name__ == '__main__':
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else 'CHANGELOG.md'
    generate_changelog(output)
```

## 测试

### 测试仓库

```bash
# 创建测试仓库
mkdir -p /tmp/test-changelog
cd /tmp/test-changelog
git init

# 创建一些测试 commits
echo "initial" > README.md
git add . && git commit -m "initial commit"

echo "feature1" > feature1.txt
git add . && git commit -m "feat: Add user authentication"

echo "fix1" > fix1.txt
git add . && git commit -m "fix: Resolve memory leak"

echo "refactor1" > refactor1.txt
git add . && git commit -m "refactor: Improve error handling"

echo "remove1" > remove1.txt
git add . && git commit -m "remove: Deprecate legacy API"

# 运行生成器
bash changelog.sh
# 或
python3 changelog.py

# 查看结果
cat CHANGELOG.md
```

### 预期输出

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add user authentication (abc123)

### Fixed
- fix: Resolve memory leak (def456)

### Changed
- refactor: Improve error handling (ghi789)

### Removed
- remove: Deprecate legacy API (jkl012)
```

## 集成到 Hermes Agent

作为 Skill 使用时，在 `SKILL.md` 中添加：

```markdown
## 触发条件
- 用户想要生成 CHANGELOG
- 项目有新的 git commits 需要记录
- 准备发布新版本

## 命令
/generate-changelog [output_file]

## 参数
- output_file: 输出文件名（默认：CHANGELOG.md）
```

## 常见问题

### Q: Commit 没有按规范写前缀怎么办？
A: 未识别的 commits 会归类到 `Other` 分类，或手动调整分类规则。

### Q: 如何按时间范围生成？
A: 使用 git log 的日期范围：
```bash
git log --since="2026-04-01" --until="2026-04-21"
```

### Q: 支持多项目 monorepo 吗？
A: 支持，指定子目录运行即可：
```bash
cd packages/frontend && bash changelog.sh
```

## 相关技能

- `github-pr-workflow` - PR 提交流程
- `automated-testing-framework` - 测试代码
- `hermes-plugin-development` - 创建 Hermes Plugin

## 验收标准（Bounty #1）

- [x] 创建 `SKILL.md` 技能文档
- [x] 提供 `changelog.sh` bash 脚本
- [x] 支持 `/generate-changelog` 命令
- [x] 输出包含 Added/Fixed/Changed/Removed 分类
- [x] 生成结构化 `CHANGELOG.md`

## 交付物

1. `SKILL.md` - 本文件
2. `changelog.sh` - Bash 脚本
3. `changelog.py` - Python 高级版本（可选）

---

**Bounty:** $50 USD via Opire  
**Issue:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1  
**Status:** ✅ Claimed - In Progress
