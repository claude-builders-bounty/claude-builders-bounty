# Changelog Generator

从 git 历史自动生成结构化 `CHANGELOG.md`。

## 3 步设置

```bash
# 1. 下载脚本
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/changelog-generator/main/changelog.sh
chmod +x changelog.sh

# 2. 在你的仓库中运行
cd your-project
bash /path/to/changelog.sh

# 3. 查看生成的 CHANGELOG.md
cat CHANGELOG.md
```

## 功能

- ✅ 自动获取最近 tag 以来的所有 commit
- ✅ 按 conventional commit 规范自动分类（Added / Fixed / Changed / Removed）
- ✅ 输出标准 Markdown 格式
- ✅ 支持任意 git 仓库
- ✅ 纯 bash 实现，零依赖

## 用法

```bash
# 默认输出到 CHANGELOG.md
bash changelog.sh

# 自定义输出文件和仓库路径
bash changelog.sh RELEASE_NOTES.md /path/to/repo
```

## Claude Code 集成

将 `SKILL.md` 复制到你项目的 `.claude/commands/` 目录，即可通过 `/generate-changelog` 命令使用。

## 分类规则

脚本根据 commit message 前缀自动分类：

| 前缀 | 分类 |
|------|------|
| `feat:`, `add:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `change:`, `update:`, `improve:`, `perf:` | Changed |
| `remove:`, `delete:` | Removed |
| 其他 | Other |
