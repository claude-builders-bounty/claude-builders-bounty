# 📜 CHANGELOG Generator - 示例输出

本文件展示CHANGELOG Generator在实际GitHub仓库中的输出效果。

---

## 示例 1: 本仓库 (n8n-weekly-summary)

运行命令：
```bash
./changelog.sh
```

输出结果：

```markdown
# Changelog

## [v0.1.0] - 2026-03-29

### Changed

- Initial commit: n8n GitHub Weekly Summary Workflow (deeb346)
```

---

## 示例 2: 模拟多commits仓库

假设有以下git历史：

```
feat: add user authentication system
fix: resolve login redirect bug  
update: improve error messages
docs: add API documentation
refactor: optimize database queries
fix: patch security vulnerability
feat: implement dark mode
delete: remove deprecated endpoints
```

生成的CHANGELOG.md：

```markdown
# Changelog

## [v1.2.3] - 2026-03-29

### Added
- add user authentication system (abc1234)
- implement dark mode (def5678)

### Fixed
- resolve login redirect bug (ghi9012)
- patch security vulnerability (jkl3456)

### Changed
- improve error messages (mno7890)
- add API documentation (pqr1234)
- optimize database queries (stu5678)

### Removed
- remove deprecated endpoints (vwx9012)
```

---

## 功能验证 ✅

- [x] 自动获取commits since last tag
- [x] 智能分类 (Added/Fixed/Changed/Removed)
- [x] 支持Conventional Commits规范
- [x] 版本号自动递增
- [x] 输出格式符合标准

---

**测试时间**: 2026-03-29
**测试者**: 蛋头先生 (龙虾战队)
