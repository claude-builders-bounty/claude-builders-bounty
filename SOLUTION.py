import argparse
import requests
import sys
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

# Default GitHub Token for API calls (if needed)
GITHUB_API_URL = "https://api.github.com"


def extract_pr_metadata(pr_url: str) -> Dict[str, str]:
    """
    Parses a GitHub PR URL to extract Owner, Repo, and Number for the API call.
    """
    # Regex to handle URLs like: https://github.com/owner/repo/pull/123
    # Also handles /pulls/ for API consistency
    match = re.search(
        r"(?:https://github\.com/)?(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?:pulls/)?(?P<num>\d+)",
        pr_url
    )
    if match:
        owner = match.group("owner")
        repo = match.group("repo")
        number = match.group("num")
        
        # Ensure owner and repo don't clash (e.g. owner/repo with owner/repo)
        # Simple logic: owner is before first /, repo is before last /
        # But regex handles the main logic.
        
        base_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{number}"
        return {
            "owner": owner,
            "repo": repo,
            "number": number,
            "full_url": base_url
        }
    return {}


def fetch_pr_data(metadata: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Fetches the raw JSON from the GitHub API.
    """
    if not metadata.get("full_url"):
        return None

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Opire-CLI-Agent"
    }
    
    try:
        # Try to get the default token from env, fallback to empty string for public access
        token = Optional[str].__call__(
            requests.get(
                metadata["full_url"],
                headers=headers,
                timeout=10
            ).json()
        ) # Simplified try/except for brevity
        
        response = requests.get(metadata["full_url"], headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 304:
            # Check ETag handling if needed, otherwise just parse
            return response.json()
        elif response.status_code == 404:
            # Handle 404 (e.g. owner mismatch)
            print(f"Note: PR might be at {metadata['full_url']}", file=sys.stderr)
            return response.json()
            
    except requests.exceptions.RequestException as e:
        # Default fallback to title if API fails or if public PR
        return {}

def analyze_diff(pr_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the JSON structure to extract summary, risks, and suggestions.
    """
    if not pr_json:
        pr_json = {}

    title = pr_json.get("title", "Review PR")
    state = pr_json.get("state", "open")
    number = pr_json.get("number", 0)
    
    # Calculate total changed lines
    files = pr_json.get("files", [])
    
    total_lines = 0
    file_names = []
    file_types = []
    is_complex = False
    
    # Heuristic: If 3+ files or >50 lines changed, confidence goes up
    risk_level = "Low"
    
    for file_obj in files:
        filename = file_obj.get("filename", "")
        additions = file_obj.get("additions", 0)
        deletions = file_obj.get("deletions", 0)
        file_types.append(filename)
        file_names.append(filename)
        total_lines += additions + deletions
        
        # Risk logic
        if "test" not in filename and filename.endswith((".py", ".js", ".ts")):
            risk_level = "High" if risk_level == "Low" else risk_level
            
    # Generate Summary (2-3 sentences)
    if total_lines > 100:
        summary = f"{title} introduces significant changes. It touches multiple files with a total of {total_lines} lines modified."
    elif total_lines > 20:
        summary = f"{title} refines the codebase. Key changes are concentrated in the existing logic with {total_lines} lines modified."
    else:
        summary = f"{title} adds a small touch to the repository. The diff is minimal, touching only {total_lines} lines."
        
    if len(files) == 1:
        file_name = files[0].get("filename", "The file")
        summary += f" It focuses primarily on {file_name}."
        
    # Generate Risks
    risks = [
        "Multiple files changed may cause merge conflicts",
        "Binary files (if any) not diffed cleanly",
        "New dependencies introduced"
    ]
    
    # Refine risks based on heuristics
    for f in files:
        fname = f.get("filename", "")
        if "vendor" in fname or "node_modules" in fname:
            risks.append(f"Third-party file modification: {fname}")
            
    # Generate Suggestions
    suggestions = [
        "Add a changelog entry for this version",
        "Update any corresponding test files",
        "Check for unused imports after deletions"
    ]
    
    # Dynamic suggestion based on file types
    if any(".py" in f for f in files):
        suggestions.append("Ensure type hints are consistent")
    if any("test" in f for f in files):
        suggestions.append("Ensure test coverage remains at parity")
        
    # Determine Confidence Score
    confidence_map = {0: "Low", 1: "Medium", 2: "High"}
    confidence = confidence_map.get(len(files), "Medium")
    if total_lines > 200: confidence = "High"
    if total_lines > 50: confidence = "High"
    
    # Fallback for empty files list
    if not files:
        files = [pr_json.get("filename", "main")]
        
    return {
        "title": title,
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "author": pr_json.get("user", {}).get("login", "Unknown")
    }

def build_markdown(analysis: Dict[str, Any]) -> str:
    """
    Constructs the final structured Markdown string.
    """
    md = f"""# PR Review for #{analysis['number']}
**By:** {analysis['author']}
**State:** {analysis['title'].capitalize()}
"""
    
    md += f"""
### 📄 Summary
{analysis['summary']}
"""
    
    md += f"""
### 🧠 Risks
- {analysis['risks'][0]}
- {analysis['risks'][1]}
"""
    
    md += f"""
### 💡 Suggestions
- {analysis['suggestions'][0]}
- {analysis['suggestions'][1]}
"""
    
    md += f"""
### 🎯 Confidence Score
**{analysis['confidence']}**

"""
    # Add file breakdown footer
    files = analysis.get("files", [])
    if files:
        md += f"""**Files touched:** {', '.join(files)}"""

    return md


def run_review(pr_url: str) -> None:
    """
    Main entry point for the CLI runner.
    """
    metadata = extract_pr_metadata(pr_url)
    
    if not metadata:
        # Fallback if regex fails, try direct API
        print(f"Attempting direct parse: {pr_url}", file=sys.stderr)
        metadata = {"owner": "default", "repo": "repo", "number": "1", "full_url": f"{GITHUB_API_URL}/repos/default/repo/pulls/1"}

    data = fetch_pr_data(metadata)
    
    if not data or not data.get("title"):
        print("No title found, fetching details...", file=sys.stderr)
        
    result = analyze_diff(data)
    result["files"] = data.get("files", []) # Inject for markdown
    
    print(build_markdown(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Opire Agent: Structured PR Review CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--pr",
        type=str,
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
    )
    
    args = parser.parse_args()
    
    if args.pr:
        run_review(args.pr)
    else:
        run_review("https://github.com/opire/agent-review/pull/1")