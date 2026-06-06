# Changelog Generator

自动从git历史生成结构化 `CHANGELOG.md` 的 Claude Code SKILL。

## 安装

```bash
# 1. 下载脚本
curl -O https://raw.githubusercontent.com/curry202504/claude-builders-bounty/main/changelog.sh

# 2. 赋予执行权限
chmod +x changelog.sh

# 3. 开箱即用
./changelog.sh
```

## 用法

```bash
./changelog.sh                    # 从最新tag生成完整CHANGELOG
./changelog.sh --since v1.0.0     # 从指定tag开始
./changelog.sh --output CHANGES.md # 自定义输出文件名
./changelog.sh --help              # 查看帮助
```

## 输出示例

```markdown
# Changelog

## [1.0.0] - 2026-06-06

### Added
- 新增用户认证模块
- 添加API限流功能

### Fixed
- 修复登录页白屏问题
- 处理空指针异常

### Changed
- 优化数据库查询性能
- 升级依赖版本

### Removed
- 移除废弃的旧API接口
```

## 分类规则

| 类型 | git commit 前缀 | CHANGELOG 分类 |
|------|-----------------|----------------|
| 新功能 | `feat:`, `add:`, `implement:`, `create:` | Added |
| 修复 | `fix:`, `bug:`, `hotfix:`, `patch:`, `resolve:` | Fixed |
| 变更 | `update:`, `change:`, `refactor:`, `migrate:`, `perf:` | Changed |
| 删除 | `remove:`, `delete:`, `deprecat:` | Removed |

## 要求

- Git >= 2.0
- Bash >= 3.0 (macOS/Linux/WSL/Git Bash)
