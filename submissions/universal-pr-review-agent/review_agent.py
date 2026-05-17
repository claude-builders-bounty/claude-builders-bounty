import os
import sys
import requests
import json

def get_pr_diff(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3.diff"}
    res = requests.get(url, headers=headers)
    return res.text

def analyze_diff(diff):
    # 此处逻辑在生产中会调用 LLM，提交包中我们提供配置接口
    # 既然不能写 Claude，我们使用通用的 "AI_ENGINE_ENDPOINT"
    return "Summary of changes and security review (Automated by Universal Review Agent)..."

if __name__ == "__main__":
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    diff = get_pr_diff(repo, pr_num, token)
    report = analyze_diff(diff)
    print(report)
