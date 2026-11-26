---
name: generate-changelog
description: 从当前 git 仓库的提交历史生成结构化 CHANGELOG.md（Added / Changed / Fixed / Removed）。当用户要求“生成更新日志 / 补 CHANGELOG / 从 git 历史总结变更”时使用。
---

# 生成 CHANGELOG

## 何时用

- 用户说“生成 changelog”“补更新日志”“把这次发布的变更整理一下”
- 准备发版，需要一份人类可读的变更清单

## 怎么做

1. 在仓库根目录运行：

   ```bash
   python3 changelog.py
   ```

   默认从**最近一个 git tag** 到 HEAD 生成；没有 tag 时取全部历史。

2. 需要指定范围或输出名时：

   ```bash
   python3 changelog.py -r v1.2.0..HEAD -o CHANGELOG.md
   ```

3. 只想看结果、不落盘：

   ```bash
   python3 changelog.py --dry-run
   ```

4. 生成后把结果贴给用户，并说明：范围、条数、哪些提交被归到哪一类。

## 分类规则（用户问起时照这个解释）

| 提交前缀 | 归类 |
| --- | --- |
| `feat` / `feature` / `add` | Added |
| `fix` / `bugfix` / `hotfix` | Fixed |
| `refactor` / `perf` / `chore` / `docs` / `update` | Changed |
| `remove` / `delete` / `drop` / `revert` | Removed |

没有前缀时，按中文关键词兜底（新增/添加 → Added，修复 → Fixed，删除/移除 → Removed），都不匹配就归 Changed。

README 更新这类 `docs:` 提交会进 Changed——如果用户不想要，加 `--exclude-docs` 之前先问一句，别自己改行为。

## 不要做

- 不要改写已有 CHANGELOG 的历史段落，只在顶部插入新版本
- 不要编造提交里没有的条目
- 命令失败（不在 git 仓库、没有 git）时，把报错原文给用户，不要猜
