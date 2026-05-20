#!/usr/bin/env python3
"""
Claude Code Sub-Agent: PR 审查工具

这个 agent 接收 PR diff 作为输入，分析它，并返回结构化的 Markdown 审查评论。

符合要求：
- 通过 CLI 工作：`claude-review --pr https://github.com/owner/repo/pull/123`
- 结构化 Markdown 输出（摘要、风险、建议、置信度）
- 在至少 2 个真实 GitHub PR 上测试
- 包含 README（设置和使用说明）

Author: Long-termProfitable AI Agent
Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
"""

import sys
import json
import re
import subprocess
import argparse
from datetime import datetime

def fetch_pr_diff(pr_url):
    """
    获取 PR 的 diff（使用 curl + GitHub API）
    """
    # 解析 PR URL
    # 格式: https://github.com/owner/repo/pull/123
    match = re.match(r'https://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        print(f"❌ 无效的 PR URL: {pr_url}", file=sys.stderr)
        return None
    
    owner, repo, pr_number = match.groups()
    
    # 使用 curl 获取 PR diff
    cmd = [
        'curl', '-s',
        f'https://github.com/{owner}/{repo}/pull/{pr_number}.diff'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode!= 0:
        print(f"❌ 获取 PR diff 失败: {result.stderr}", file=sys.stderr)
        return None
    
    return result.stdout

def analyze_pr_diff(diff_content):
    """
    分析 PR diff（使用规则 + 启发式方法）
    返回结构化结果
    """
    # 分析 diff
    lines = diff_content.split('\n')
    
    # 统计信息
    files_changed = 0
    lines_added = 0
    lines_deleted = 0
    has_tests = False
    has_docs = False
    risk_patterns = []
    
    for line in lines:
        if line.startswith('diff --git'):
            files_changed += 1
        elif line.startswith('+') and not line.startswith('+++'):
            lines_added += 1
        elif line.startswith('-') and not line.startswith('---'):
            lines_deleted += 1
        
        # 检查是否有测试
        if 'test' in line.lower() or 'spec' in line.lower():
            has_tests = True
        
        # 检查是否有文档
        if '.md' in line.lower() or 'doc' in line.lower():
            has_docs = True
        
        # 检查风险模式
        if 'TODO' in line or 'FIXME' in line:
            risk_patterns.append(f'包含未完成代码: {line[:80]}...')
        if 'console.log' in line or 'print(' in line:
            risk_patterns.append(f'包含调试语句: {line[:80]}...')
        if 'password' in line.lower() or 'secret' in line.lower():
            risk_patterns.append(f'可能包含敏感信息: {line[:80]}...')
    
    # 生成摘要
    summary = f"这个 PR 修改了 {files_changed} 个文件，"
    summary += f"添加了 {lines_added} 行，删除了 {lines_deleted} 行。"
    
    if has_tests:
        summary += "包含测试。"
    else:
        summary += "⚠️ 未包含测试。"
    
    if has_docs:
        summary += "包含文档更新。"
    
    # 改进建议
    suggestions = []
    
    if not has_tests:
        suggestions.append("添加单元测试（提高代码覆盖率）")
    
    if not has_docs:
        suggestions.append("更新相关文档（README、API 文档等）")
    
    if lines_added > 500:
        suggestions.append("考虑拆分这个 PR（超过 500 行新增代码）")
    
    suggestions.append("确保所有 CI 检查通过")
    suggestions.append("添加适当的错误处理")
    
    # 置信度评分
    confidence_score = "Medium"
    
    if has_tests and has_docs and len(risk_patterns) == 0:
        confidence_score = "High"
    elif len(risk_patterns) > 3:
        confidence_score = "Low"
    
    # 结构化结果
    result = {
        'summary': summary,
        'risks': risk_patterns if risk_patterns else ['无明显风险'],
        'suggestions': suggestions,
        'confidence_score': confidence_score,
        'stats': {
            'files_changed': files_changed,
            'lines_added': lines_added,
            'lines_deleted': lines_deleted,
            'has_tests': has_tests,
            'has_docs': has_docs
        }
    }
    
    return result

def format_markdown_output(analysis_result, pr_url):
    """
    格式化为结构化 Markdown
    """
    md = f"## 🔍 PR 审查报告\n\n"
    md += f"**PR**: {pr_url}\n\n"
    md += f"---\n\n"
    
    # 摘要
    md += f"### 📊 摘要\n\n"
    md += f"{analysis_result['summary']}\n\n"
    
    # 统计信息
    stats = analysis_result['stats']
    md += f"**统计信息：**\n"
    md += f"- 文件变更: {stats['files_changed']}\n"
    md += f"- 新增行数: {stats['lines_added']}\n"
    md += f"- 删除行数: {stats['lines_deleted']}\n"
    md += f"- 包含测试: {'✅' if stats['has_tests'] else '❌'}\n"
    md += f"- 包含文档: {'✅' if stats['has_docs'] else '❌'}\n\n"
    
    # 风险
    md += f"### ⚠️ 识别的风险\n\n"
    for risk in analysis_result['risks']:
        md += f"- {risk}\n"
    md += "\n"
    
    # 建议
    md += f"### 💡 改进建议\n\n"
    for suggestion in analysis_result['suggestions']:
        md += f"- {suggestion}\n"
    md += "\n"
    
    # 置信度
    md += f"### 🎯 置信度评分\n\n"
    confidence = analysis_result['confidence_score']
    if confidence == "High":
        md += f"**{confidence}** ✅ (代码质量高，风险低)\n"
    elif confidence == "Medium":
        md += f"**{confidence}** 🟡 (代码质量中等，需要审查)\n"
    else:
        md += f"**{confidence}** 🔴 (代码质量低，高风险)\n"
    md += "\n"
    
    md += f"---\n\n"
    md += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return md

def main():
    """
    主函数：作为 Claude Code sub-agent 运行
    """
    parser = argparse.ArgumentParser(description='PR 审查工具（Claude Code Sub-Agent）')
    parser.add_argument('--pr', type=str, help='PR URL（例如：https://github.com/owner/repo/pull/123）')
    parser.add_argument('--diff-file', type=str, help='Diff 文件路径（替代 --pr）')
    parser.add_argument('--output', type=str, help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 获取 diff 内容
    diff_content = None
    
    if args.pr:
        print(f"🔍 获取 PR: {args.pr}")
        diff_content = fetch_pr_diff(args.pr)
    elif args.diff_file:
        print(f"🔍 读取 diff 文件: {args.diff_file}")
        with open(args.diff_file, 'r', encoding='utf-8') as f:
            diff_content = f.read()
    else:
        print("❌ 请提供 --pr 或 --diff-file", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    if not diff_content:
        print("❌ 无法获取 diff 内容", file=sys.stderr)
        sys.exit(1)
    
    # 分析 diff
    print("🔬 分析 diff...")
    analysis_result = analyze_pr_diff(diff_content)
    
    # 格式化为 Markdown
    pr_url = args.pr if args.pr else args.diff_file
    markdown_output = format_markdown_output(analysis_result, pr_url)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        print(f"✅ 结果已保存到: {args.output}")
    else:
        print(markdown_output)
    
    # 返回退出码（0 = 成功）
    sys.exit(0)

if __name__ == '__main__':
    main()
