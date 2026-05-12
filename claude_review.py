#!/usr/bin/env python3
"""claude-review: Claude Code PR审查工具
接受PR URL，分析diff，返回结构化Markdown审查评论。

用法:
    python claude_review.py --pr <PR_URL>
    claude-review --pr <PR_URL>  # 安装后
"""

import sys
import json
import urllib.request
import urllib.error
import re

TOKEN = ""  # 使用环境变量GITHUB_TOKEN，或在此填写
API = "https://api.github.com"

def api_get(path, accept_header="application/vnd.github.v3+json"):
    url = API + path
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {TOKEN}" if TOKEN else "")
    req.add_header("Accept", accept_header)
    req.add_header("User-Agent", "claude-review-agent")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode()
    except Exception as e:
        print(f"API请求失败: {e}")
        return None

def get_pr_diff(pr_url):
    """获取PR的diff内容"""
    m = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        print(f"无法解析PR URL: {pr_url}")
        return None, None, None
    
    owner, repo, pr_num = m.group(1), m.group(2), m.group(3)
    print(f"获取 {owner}/{repo} PR #{pr_num} 的diff...")
    
    # 获取diff
    diff = api_get(f"/repos/{owner}/{repo}/pulls/{pr_num}", "application/vnd.github.v3.diff")
    if not diff:
        return None, None, None
    
    # 获取PR元信息
    pr_data_raw = api_get(f"/repos/{owner}/{repo}/pulls/{pr_num}")
    pr_data = json.loads(pr_data_raw) if pr_data_raw else {}
    
    print(f"  ✅ 获取diff成功 ({len(diff)} 字符)")
    return diff, owner, repo

def analyze_diff(diff_text, pr_data=None):
    """分析diff，生成结构化审查评论"""
    print("  分析diff...")
    
    # 统计变化
    additions = diff_text.count('\n+') - diff_text.count('\n+++')
    deletions = diff_text.count('\n-') - diff_text.count('\n---')
    files_changed = diff_text.count('diff --git')
    
    # 生成审查评论
    review = f"""## 🤖 Claude Code PR Review

### 📊 变更概览
| 指标 | 数值 |
|------|------|
| 变更文件数 | {files_changed} |
| 新增行数 | +{additions} |
| 删除行数 | -{deletions} |
| 净变化 | {additions - deletions:+} 行 |

### 🔍 审查意见

"""
    
    warnings = []
    suggestions = []
    
    diff_lower = diff_text.lower()
    
    # 规则检查
    if additions > 500:
        warnings.append("⚠️ **大PR警告**: 本次变更超过500行新增，建议拆分为多个小PR，便于review。")
    
    if 'todo' in diff_lower or 'fixme' in diff_lower:
        warnings.append("⚠️ **未完成标记**: diff中发现`TODO`或`FIXME`标记，请确认是否需要处理。")
    
    if 'print(' in diff_text or 'console.log' in diff_text:
        warnings.append("⚠️ **调试代码**: 发现`print()`或`console.log()`等调试语句，建议删除。")
    
    if 'password' in diff_lower or 'secret' in diff_lower or 'api_key' in diff_lower:
        warnings.append("🚨 **安全风险**: diff中出现敏感关键词，请确认无敏感信息泄露。")
    
    if files_changed > 10:
        warnings.append("⚠️ **多文件变更**: 本次变更涉及多个文件，请确保每个文件的修改都是必要的。")
    
    # 检查是否有测试
    has_test = 'test' in diff_lower or 'spec' in diff_lower
    if not has_test and additions > 50:
        suggestions.append("💡 **建议添加测试**: 本次变更为业务逻辑，建议添加相应测试用例。")
    
    if warnings:
        review += "#### ⚠️ 警告\n"
        for w in warnings:
            review += f"- {w}\n"
        review += "\n"
    
    if suggestions:
        review += "#### 💡 建议\n"
        for s in suggestions:
            review += f"- {s}\n"
        review += "\n"
    
    if not warnings and not suggestions:
        review += "#### ✅ 审查通过\n未发现明显问题，请其他reviewer确认。\n\n"
    
    review += f"""#### 📝 统计
- 变更文件: {files_changed} 个
- 代码行变化: +{additions}/-{deletions}

---

*此评论由 `claude-review` 工具自动生成。*
"""
    
    print(f"  ✅ 分析完成，生成 {len(review)} 字符的审查评论")
    return review

def main():
    if len(sys.argv) < 2:
        print("用法: python claude_review.py --pr <PR_URL>")
        print("示例: python claude_review.py --pr https://github.com/owner/repo/pull/123")
        sys.exit(1)
    
    pr_url = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
    
    print("=" * 60)
    print("Claude Code PR Review Agent")
    print("=" * 60)
    
    # 获取diff
    diff_text, owner, repo = get_pr_diff(pr_url)
    if not diff_text:
        sys.exit(1)
    
    # 分析
    review_comment = analyze_diff(diff_text)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("生成的审查评论:")
    print("=" * 60)
    print(review_comment)
    print("=" * 60)
    
    print("\n💡 要发布此评论到PR，请手动复制上方评论并粘贴到PR页面")
    print(f"   PR链接: {pr_url}")

if __name__ == "__main__":
    main()
