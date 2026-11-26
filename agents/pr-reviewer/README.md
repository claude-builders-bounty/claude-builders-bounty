# claude-review

给一个 GitHub PR 地址，回一份结构化的 Markdown 评审：**改动概述 / 风险 / 改进建议 / 置信度**。

```console
$ python3 claude_review.py --pr https://github.com/pallets/flask/pull/6168
```

没有任何依赖（标准库），没有 API key 也能跑——分析基于真实 diff，不编。

## 安装

```bash
git clone https://github.com/<you>/claude-review ~/.local/share/claude-review
ln -s ~/.local/share/claude-review/claude_review.py ~/.local/bin/claude-review
chmod +x ~/.local/bin/claude-review
```

私有仓库要读的话，导出 `GITHUB_TOKEN`（只读 `pull_requests` 权限就够）。

## 用法

```bash
# 打一份到终端
claude-review --pr https://github.com/owner/repo/pull/123

# 存成文件
claude-review --pr owner/repo#123 --out review.md

# 看本地未提交的 diff
git diff main...HEAD > /tmp/x.diff
claude-review --diff /tmp/x.diff --title "feat: something"
```

## 输出长什么样

见 `samples/`：一个是 Python 钩子 PR（`pr-5314-hook.md`），一个是外部仓库的真实 PR
（`pr-flask-6168.md`）。两个都是对真实 diff 跑的。

结构固定：

```markdown
## 评审
**PR**：<标题>

### 改动概述
2–3 句：改了多少文件、增删行数、集中在哪、有没有带测试

### 风险
- **[high]** 包含破坏性 SQL（DROP / TRUNCATE）
- **[medium]** 改了代码但没带测试

### 改进建议
- ...

### 置信度
**Low / Medium / High**
```

## 判断逻辑

**确定性层（永远跑）**：从 diff 里数文件、增删行、目录分布，扫已知风险模式——
破坏性 SQL、无 `WHERE` 的 `DELETE`、硬编码密钥、`chmod 777`、`--no-verify`、
关闭 CSRF/SSL 校验、迁移文件、锁文件变动。

两个降噪规则是踩过坑才加的：

- `tests/`、`samples/`、`*.md` 里的危险字样不算风险（夹具和文档会大量出现）。
- 只有当词出现在**执行上下文**里才算（`execute(`、`cursor.`、`subprocess.run(` 等）；
  只是写在一句提示语里的 `DROP TABLE` 不报。这就是为什么评审一个“检测危险命令的
  钩子”不会被它自己的字符串骗到。

**模型层（可选）**：设了 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` 时，把确定性结论交给
模型写成 2–3 句摘要；调不通就静默退回模板，不阻塞。

## 置信度怎么算

| 情况 | 置信度 |
| --- | --- |
| 命中任一 high 风险 | Low |
| 风险 ≥ 3 条，或新增 > 500 行 | Medium |
| 其它 | High |

含义是“这份自动评审有多可信”，不是“代码有多好”。

## 作为 GitHub Action

`.github/workflows/claude-review.yml` 已经写好：PR 打开/更新时跑一次，
把评审贴成评论。要模型润色就在仓库 secrets 里加 `ANTHROPIC_API_KEY`。

## 已知边界

- 静态启发式，不是语义分析：重构型 PR 可能被判定为“没风险”。
- 只看 diff，不看仓库上下文；跨文件影响判断不了。
- 没有 `GITHUB_TOKEN` 时只能读公开仓库。
