# /generate-changelog

从当前仓库的 git 历史自动生成结构化 `CHANGELOG.md`。

## 用法

```
/generate-changelog
```

## 执行步骤

1. 获取最近的 git tag（没有则从首次 commit 开始）
2. 提取该范围内的所有非 merge commit
3. 按 conventional commit 前缀分类：`feat:` → Added, `fix:` → Fixed, `refactor:`/`update:` → Changed, `remove:` → Removed
4. 输出格式化的 `CHANGELOG.md` 到仓库根目录

## 分类规则

| 前缀 | 分类 |
|------|------|
| `feat:`, `add:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `change:`, `update:`, `improve:`, `perf:` | Changed |
| `remove:`, `delete:` | Removed |
| 其他 | Other |

## 输出格式

```markdown
# Changelog

## [tag] — YYYY-MM-DD

### Added
- 描述 (`hash`)

### Fixed
- 描述 (`hash`)
```

## 注意事项

- 跳过 merge commit，只保留实际改动
- 自动检测当前日期
- 输出文件默认为 `CHANGELOG.md`，可通过参数自定义
