import subprocess
import os
import sys
import json
import http.client

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except:
        return ""

def get_commits():
    try:
        # Get the last tag
        last_tag = run_cmd("git describe --tags --abbrev=0")
        if not last_tag:
            range_str = "HEAD"
        else:
            range_str = f"{last_tag}..HEAD"
    except:
        range_str = "HEAD"
        
    commits = run_cmd(f"git log {range_str} --pretty=format:'%s'")
    return commits

def call_claude(commits):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fallback to local summarization if no key is present for the demo
        return f"## [Unreleased]\n### Added\n" + "\n".join([f"- {c}" for b in commits.split('\n') if (c := b.strip())])

    prompt = f"Categorize the following git commits into Added, Fixed, Changed, and Removed. Output a structured CHANGELOG.md section for the current version.\n\nCommits:\n{commits}"
    
    payload = json.dumps({
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }
    
    try:
        conn = http.client.HTTPSConnection("api.anthropic.com")
        conn.request("POST", "/v1/messages", payload, headers)
        res = conn.getresponse()
        data = res.read()
        if res.status != 200:
            return None
        return json.loads(data.decode())["content"][0]["text"]
    except:
        return None

if __name__ == "__main__":
    commits = get_commits()
    if not commits:
        print("No new commits found.")
        sys.exit(0)
        
    changelog = call_claude(commits)
    if changelog:
        print(changelog)
