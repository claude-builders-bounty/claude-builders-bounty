import requests
import json

# Fetch repo contents
repo_url = "https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty"
issue_url = f"{repo_url}/issues/4"

print("Fetching repo info...")
repo = requests.get(repo_url).json()
print(f"Repo: {repo.get('full_name', 'N/A')}")
print(f"Description: {repo.get('description', 'N/A')}")

print("\nFetching issue #4...")
issue = requests.get(issue_url).json()
print(f"Title: {issue.get('title', 'N/A')}")
print(f"Body:\n{issue.get('body', 'N/A')}")
print(f"State: {issue.get('state', 'N/A')}")
print(f"Labels: {[l['name'] for l in issue.get('labels', [])]}")
