# generate-changelog

从 git 历史生成一份结构化 `CHANGELOG.md`（Added / Changed / Fixed / Removed），
支持 conventional commit 前缀和中文关键词。

## 三步用起来

```bash
# 1. 放到仓库根目录（changelog.py 与仓库同级）
# 2. 运行
python3 changelog.py

# 3. 看结果
cat CHANGELOG.md
```

等价的一行版（bash 环境）：

```bash
bash changelog.sh
```

## 参数

| 参数 | 说明 |
| --- | --- |
| `-o, --output` | 输出文件名，默认 `CHANGELOG.md` |
| `-r, --range` | 提交范围，如 `v1.2.0..HEAD`；默认最近 tag 到 HEAD |
| `--dry-run` | 只打印到终端，不写文件 |

## 生成的样例

仓库 `demo/` 里有 8 个提交、一个 `v0.1.0` tag，运行后得到
[`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md)。

## 分类规则

| 提交前缀 | 归类 |
| --- | --- |
| `feat` `feature` `add` | Added |
| `fix` `bugfix` `hotfix` | Fixed |
| `refactor` `perf` `chore` `docs` `update` | Changed |
| `remove` `delete` `drop` `revert` | Removed |

无前缀时按关键词兜底：新增/添加 → Added，修复 → Fixed，删除/移除 → Removed，
其余一律 Changed。

## 依赖

- Python 3.8+
- git

## 也提供 Claude Code Skill

仓库里的 `SKILL.md` 可以直接作为 Claude Code skill 使用：
放到 `~/.claude/skills/generate-changelog/` 下，触发词是“生成 changelog / 补更新日志”。
