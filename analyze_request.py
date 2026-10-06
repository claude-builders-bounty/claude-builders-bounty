```python
import urllib.request
import json

# Fetch repo contents
req = urllib.request.Request("https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    repo = json.load(resp)
    print("Repo:", repo.get("default_branch"), repo.get("description"))

# Fetch issue #3808
req2 = urllib.request.Request("https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty/issues/3808", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=10) as resp2:
    issue = json.load(resp2)
    print("Issue title:", issue.get("title"))
    print("Issue body:", issue.get("body"))
    print("Issue state:", issue.get("state"))
    print("Issue assignee:", issue.get("assignee", {}).get("login") if issue.get("assignee") else None)

# List branches
req3 = urllib.request.Request("https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty/branches", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req3, timeout=10) as resp3:
    branches = json.load(resp3)
    for b in branches[:10]:
        print("Branch:", b["name"])

# List root files
req4 = urllib.request.Request("https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty/git/trees/main?recursive=1", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req4, timeout=10) as resp4:
    tree = json.load(resp4)
    for item in tree.get("tree", [])[:50]:
        print(item["path"], item["type"])
