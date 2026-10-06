```python
import requests
import json
import os

repo = "claude-builders-bounty/claude-builders-bounty"

# Get issue #2
issue = requests.get(f"https://api.github.com/repos/{repo}/issues/2").json()
print("ISSUE TITLE:", issue.get("title"))
print("ISSUE BODY:", issue.get("body"))
print("ISSUE STATE:", issue.get("state"))

# Get repo contents
contents = requests.get(f"https://api.github.com/repos/{repo}/contents").json()
print("\nREPO STRUCTURE:")
for item in contents:
    print(f"  {item['type']}: {item['name']}")
