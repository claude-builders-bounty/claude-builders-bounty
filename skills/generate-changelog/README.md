# generate-changelog

零依赖、跨平台（仅 `bash` + `git`）的 CHANGELOG 生成器。从 git 历史
（**上一个 tag 之后**）自动生成 [Keep a Changelog](https://keepachangelog.com/) 格式的
`CHANGELOG.md`，并按 Conventional Commits 前缀 / 中文关键词把提交归类为
**Added / Fixed / Changed / Removed**。

可经 `bash changelog.sh` 直接运行，或作为 Claude Code 技能以 `/generate-changelog` 调用。

## 安装（3 步以内）

1. 把 `changelog.sh` 与 `SKILL.md` 放进项目（或 `git clone` 本仓库的 `skills/generate-changelog/`）。
2. 赋予执行权限：`chmod +x changelog.sh`。
3. 运行：`bash changelog.sh`（或在 Claude Code 中输入 `/generate-changelog`）。

## 用法

```bash
bash changelog.sh                         # 在当前仓库生成 CHANGELOG.md
bash changelog.sh --dry-run               # 仅打印到终端，不写文件
bash changelog.sh --since-tag v1.2.0 --version v1.3.0
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## 分类规则

| 分类 | Conventional Commits | 中文关键词 |
|------|----------------------|-----------|
| Added | `feat:` / `feature:` / `add:` | 新增、添加、增加、新功能、支持 |
| Fixed | `fix:` / `bug:` / `hotfix:` | 修复、修正、解决、修补 |
| Changed | `refactor:` / `perf:` / `chore:` / `build:` / `ci:` / `update:` / `docs:` | 重构、优化、改进、升级、更新、调整、修改 |
| Removed | `remove:` / `rm:` / `delete:` | 删除、移除、去掉 |

未匹配到关键词的提交归入 **Changed**（绝不丢失）。仓库无 tag 时自动回退到完整历史并注明。

## 实测

已在真实 GitHub 仓库验证运行（见 `examples/SAMPLE_CHANGELOG.md`）。
兼容性：macOS 默认 bash 3.2 与 Linux bash 4+ 均通过测试。

## 文件

- `changelog.sh` — 生成器本体（零依赖）
- `SKILL.md` — Claude Code 技能定义（`/generate-changelog`）
- `examples/SAMPLE_CHANGELOG.md` — 真实仓库的产出样例
- `tests/test_changelog.sh` — 便携自检脚本（创建临时仓库断言四类分类）
