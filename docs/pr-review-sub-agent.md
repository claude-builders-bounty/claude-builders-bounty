# AGENT: PR Review Sub-Agent for Claude Code — 技术实现文档

## 概述

本任务旨在为 Claude Code 构建一个专用的子代理（sub-agent），该代理能够自动审查 GitHub Pull Request，并生成结构化、可操作的评论。该子代理通过分析 PR 的 diff、commit 消息、关联 issue 以及仓库上下文，输出包含代码质量、潜在缺陷、安全风险、性能影响等维度的结构化反馈。

核心目标：减少人工审查负担，提升代码审查的一致性和可追溯性。子代理作为 Claude Code 的扩展，通过 CLI 或 API 触发，输出 Markdown 格式的评论，可直接发布到 PR 讨论线程。

## 详细说明

### 1. 架构设计

子代理基于以下组件构建：

- **输入层**：接收 PR 元数据（repo, PR number, base/head SHA），通过 GitHub API 获取 diff、commit 列表、changed files。
- **分析引擎**：使用 Claude Code 的代码理解能力，结合预定义的审查规则（如 ESLint 风格规则、安全模式库），对 diff 进行逐文件、逐行分析。
- **输出层**：生成结构化评论，包含摘要、分类问题列表、改进建议、优先级标签。

### 2. 关键功能模块

#### 2.1 PR 数据获取模块

```python
# 示例：使用 PyGithub 获取 PR 数据
from github import Github

def fetch_pr_data(repo_name: str, pr_number: int, token: str) -> dict:
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    return {
        "title": pr.title,
        "body": pr.body,
        "commits": [c.commit.message for c in pr.get_commits()],
        "files": [
            {
                "filename": f.filename,
                "status": f.status,
                "patch": f.patch,
                "additions": f.additions,
                "deletions": f.deletions
            }
            for f in pr.get_files()
        ],
        "base_sha": pr.base.sha,
        "head_sha": pr.head.sha
    }
```

#### 2.2 分析规则引擎

定义规则集（ruleset），每个规则包含：
- `name`: 规则名称
- `severity`: critical / major / minor / info
- `pattern`: 匹配模式（正则或 AST 模式）
- `message`: 默认提示信息
- `fix_suggestion`: 修复建议（可选）

```json
{
  "rules": [
    {
      "name": "hardcoded-secret",
      "severity": "critical",
      "pattern": "(?i)(password|secret|api_key|token)\\s*[:=]\\s*['\"][^'\"]+['\"]",
      "message": "检测到硬编码密钥，请使用环境变量或密钥管理服务",
      "fix_suggestion": "替换为 os.getenv('SECRET_KEY') 或类似方法"
    },
    {
      "name": "missing-error-handling",
      "severity": "major",
      "pattern": "try:\\s*\\n(?:\\s{4}.+\\n)+\\s*except\\s*:",
      "message": "裸 except 捕获所有异常，应指定具体异常类型",
      "fix_suggestion": "except ValueError as e: 或 except (TypeError, KeyError):"
    }
  ]
}
```

#### 2.3 评论生成模块

生成结构化评论，格式如下：

```markdown
## PR 审查报告

### 摘要
- **总文件数**: 5
- **新增行**: 120
- **删除行**: 30
- **问题总数**: 3 (Critical: 1, Major: 1, Minor: 1)

### 问题列表

#### 🔴 Critical: 硬编码密钥
- **文件**: `src/config.py` 第 42 行
- **描述**: 检测到 API 密钥直接写在代码中
- **建议**: 使用 `os.getenv("API_KEY")` 从环境变量读取
- **代码片段**:
  ```python
  # 当前
  API_KEY = "sk-abc123..."
  # 建议
  API_KEY = os.getenv("API_KEY")
  ```

#### 🟡 Major: 裸 except
- **文件**: `src/processor.py` 第 15-18 行
- **描述**: 捕获所有异常，可能隐藏错误
- **建议**: 改为 `except FileNotFoundError:`

#### 🔵 Minor: 未使用的导入
- **文件**: `src/main.py` 第 3 行
- **描述**: `import json` 未被使用
- **建议**: 移除未使用的导入

### 改进建议
1. **测试覆盖率**: 新增逻辑未包含单元测试，建议补充
2. **文档**: 函数 `process_data` 缺少 docstring
3. **性能**: 循环中重复调用 `get_user()`，建议缓存结果
```

## 示例

### 触发命令

```bash
# 通过 CLI 触发子代理
claude-code pr-review --repo owner/repo --pr 42 --token $GITHUB_TOKEN

# 或通过 API
curl -X POST https://api.claude-code.ai/v1/pr-review \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"repo": "owner/repo", "pr_number": 42}'
```

### 实际输出示例

假设 PR 修改了 `src/api.py` 和 `src/utils.py`，子代理输出：

```markdown
## PR 审查报告

### 摘要
- **总文件数**: 2
- **新增行**: 45
- **删除行**: 12
- **问题总数**: 2

### 问题列表

#### 🟡 Major: 未处理的 JSON 解析异常
- **文件**: `src/api.py` 第 10 行
- **描述**: `json.loads(response.text)` 未捕获 `json.JSONDecodeError`
- **建议**: 添加 try-except 块
- **代码**:
  ```python
  # 当前
  data = json.loads(response.text)
  # 建议
  try:
      data = json.loads(response.text)
  except json.JSONDecodeError as e:
      logging.error(f"Invalid JSON: {e}")
      return None
  ```

#### 🔵 Minor: 魔法数字
- **文件**: `src/utils.py` 第 22 行
- **描述**: 使用 `time.sleep(5)` 但 5 的含义不明确
- **建议**: 定义为常量 `RETRY_DELAY = 5`

### 改进建议
- 建议在 `src/api.py` 中添加重试逻辑，当前没有处理网络波动
- 建议在 `src/utils.py` 中添加类型注解
```

## 注意事项

### 1. 安全性
- 子代理需要访问 GitHub API Token，建议使用只读权限的 token，且限制为特定仓库
- 分析过程中不将代码内容发送到第三方服务（除 Claude Code 自身 API 外）
- 硬编码密钥检测应避免误报，例如测试代码中的假密钥

### 2. 性能优化
- 对于大型 PR（超过 500 行 diff），建议分块分析，避免单次请求超时
- 缓存已分析的仓库元数据（如文件结构、历史模式），减少重复 API 调用
- 使用异步请求并行获取多个文件的分析结果

### 3. 自定义规则
- 规则集应支持 YAML/JSON 配置，允许团队自定义
- 支持按文件路径模式（如 `*.py`、`*.js`）应用不同规则
- 规则优先级：项目级规则 > 组织级规则 > 默认规则

### 4. 集成方式
- **GitHub Actions**: 作为 workflow 步骤运行，自动评论 PR
- **GitHub App**: 通过 webhook 触发，实时反馈
- **CLI 工具**: 本地调试或 CI 流水线中使用

### 5. 局限性
- 无法检测跨文件逻辑错误（如函数调用链问题）
- 对动态语言（Python/JS）的类型错误检测有限
- 无法替代人工审查中的业务逻辑理解

## 扩展建议

1. **增量审查**: 只分析新增/修改的行，忽略未变更部分
2. **学习模式**: 根据历史 PR 审查反馈，自动调整规则权重
3. **多语言支持**: 通过插件系统支持 Go、Rust、Java 等语言
4. **与 CI 集成**: 设置阈值（如 Critical 问题 > 0 则阻止合并）

---

**文档版本**: 1.0  
**最后更新**: 2025-04-10  
**适用场景**: 基于 Claude Code 的自动化 PR 审查代理