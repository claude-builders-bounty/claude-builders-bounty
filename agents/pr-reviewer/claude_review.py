#!/usr/bin/env python3
"""
Claude Code PR Reviewer Sub-Agent
Analyzes GitHub Pull Request diffs and outputs structured Markdown review comments.
Compliant with Claude Builders Bounty #4 acceptance criteria.
Adversarially hardened against injection, SSRF, rate-limit starvation, and secret leakage.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

REVIEW_PROMPT_TEMPLATE = """You are an expert senior code reviewer and security auditor.
Analyze the following Pull Request details and diff thoroughly.

PR Title: {title}
PR Author: {author}
Target Branch: {base_ref} <- Source Branch: {head_ref}
PR Description:
{description}

=== GIT DIFF BEGIN ===
{diff}
=== GIT DIFF END ===
{truncation_note}
You MUST produce a structured code review in strict Markdown format adhering to the following schema:

## 🤖 Claude Code PR Review

### 📋 Summary of Changes
Provide exactly 2 to 3 concise, high-impact sentences summarizing what changed, the architectural intent, and key files touched.

### ⚠️ Identified Risks
Provide a bulleted list of potential risks, security vulnerabilities, edge cases, breaking changes, or concurrency/performance issues. If no critical risks are found, highlight defensive edge cases or test gaps.
- **[Security / Stability / Performance / Edge Case]**: Description of the risk and potential blast radius.

### 💡 Improvement Suggestions
Provide a bulleted list of actionable, concrete suggestions for cleaner code, idiomatic patterns, enhanced test coverage, or documentation.
- **[Refactor / Architecture / Best Practice / Testing]**: Specific actionable suggestion with code pointers where relevant.

### 🎯 Confidence Score
State the confidence rating clearly on the first line:
**Confidence: [High | Medium | Low]**
Follow with 1-2 sentences explaining why this score was assigned based on the diff complexity, test coverage, and blast radius.

Do NOT include any extra introductory or concluding chatter outside of this Markdown structure.
"""

SAFE_IDENT_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
ALLOWED_API_DOMAINS = {"api.anthropic.com", "127.0.0.1", "localhost", "api.exman.ai"}

def sanitize_error(err_str: str) -> str:
    """Masks authorization tokens, API keys, and private credentials from logs and outputs."""
    if not isinstance(err_str, str):
        err_str = str(err_str)
    s = re.sub(r'(Bearer\s+[A-Za-z0-9_\-\.]{15,}|ghp_[A-Za-z0-9_]{30,}|sk-ant-[A-Za-z0-9_\-]{30,}|sk-proj-[A-Za-z0-9_\-]{30,}|github_pat_[A-Za-z0-9_]{30,})', '[REDACTED_CREDENTIAL]', err_str)
    return s

def validate_identifier(owner: str, repo: str, pr_num: int) -> Tuple[str, str, int]:
    """Strictly validates repo name, owner, and PR number to prevent command or argument injection."""
    if not SAFE_IDENT_REGEX.match(owner):
        raise ValueError(f"Invalid owner format: '{owner}'")
    if not SAFE_IDENT_REGEX.match(repo):
        raise ValueError(f"Invalid repository format: '{repo}'")
    if not isinstance(pr_num, int) or pr_num <= 0 or pr_num > 1_000_000_000:
        raise ValueError(f"Invalid PR number: {pr_num}")
    return owner, repo, pr_num

def validate_api_base(api_base: str) -> str:
    """Validates API base URL against SSRF target whitelist."""
    parsed = urllib.parse.urlparse(api_base)
    hostname = parsed.hostname or ""
    if hostname.lower() not in ALLOWED_API_DOMAINS:
        raise ValueError(f"SSRF Protection: api_base '{api_base}' is not in allowed domain whitelist.")
    return api_base

def parse_pr_identifier(pr_arg: str) -> Tuple[str, str, int]:
    """
    Parses PR identifier into (owner, repo, pr_number).
    Accepts:
      - https://github.com/owner/repo/pull/123
      - owner/repo#123
      - 123 (if inside a git repo with a github remote)
    """
    cleaned = pr_arg.strip()
    # Pattern 1: Full URL
    m = re.match(r"^https?://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/pull/(\d+)/?$", cleaned)
    if m:
        return validate_identifier(m.group(1), m.group(2), int(m.group(3)))

    # Pattern 2: owner/repo#123
    m = re.match(r"^([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)#(\d+)$", cleaned)
    if m:
        return validate_identifier(m.group(1), m.group(2), int(m.group(3)))

    # Pattern 3: PR number alone
    if cleaned.isdigit():
        pr_num = int(cleaned)
        try:
            res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, check=True)
            url = res.stdout.strip()
            m = re.search(r"github\.com[:/]([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?$", url)
            if m:
                return validate_identifier(m.group(1), m.group(2), pr_num)
        except Exception:
            pass

    raise ValueError(f"Could not parse GitHub PR identifier from: '{pr_arg}'. Expected 'https://github.com/owner/repo/pull/<num>' or 'owner/repo#<num>'")

def execute_with_retry(req: urllib.request.Request, max_retries: int = 3, timeout: int = 30) -> Tuple[int, bytes, Dict[str, str]]:
    """Executes HTTP request with exponential backoff and rate limit recovery."""
    delay = 1.5
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                headers = {k.lower(): v for k, v in resp.getheaders()}
                return resp.status, resp.read(), headers
        except urllib.error.HTTPError as e:
            status = e.code
            err_headers = {k.lower(): v for k, v in e.headers.items()}
            err_body = e.read()
            if status == 401:
                raise RuntimeError("GitHub Authentication Failed (HTTP 401). Verify GITHUB_TOKEN permissions.")
            if status in (403, 429):
                rem = err_headers.get("x-ratelimit-remaining", "")
                reset_ts = err_headers.get("x-ratelimit-reset", "")
                if rem == "0" and reset_ts:
                    try:
                        wait_sec = min(max(1, int(reset_ts) - int(time.time())), 60)
                        if attempt < max_retries:
                            time.sleep(wait_sec)
                            continue
                    except Exception:
                        pass
                raise RuntimeError(f"GitHub API Forbidden / Rate Limited (HTTP {status}). Check GITHUB_TOKEN or IP limits.")
            if status in (500, 502, 503, 504) and attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            safe_err = sanitize_error(err_body.decode("utf-8", errors="replace"))
            raise RuntimeError(f"HTTP Error {status}: {safe_err}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"Network error after {max_retries} attempts: {sanitize_error(str(e))}")
    raise RuntimeError("Max retries exceeded without response.")

def get_paginated_changed_files(owner: str, repo: str, pr_num: int, headers: Dict[str, str]) -> List[str]:
    """Fetches full list of changed filenames across all pages."""
    file_list = []
    page = 1
    while page <= 10:  # safety ceiling 1000 files
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}/files?page={page}&per_page=100"
        req = urllib.request.Request(api_url, headers=headers)
        try:
            status, raw_json, resp_headers = execute_with_retry(req, max_retries=2, timeout=20)
            items = json.loads(raw_json.decode("utf-8"))
            if not items:
                break
            for item in items:
                fn = item.get("filename")
                if fn:
                    file_list.append(fn)
            if len(items) < 100:
                break
            page += 1
        except Exception:
            break
    return file_list

def get_pr_metadata_and_diff(owner: str, repo: str, pr_num: int) -> Tuple[Dict[str, Any], str]:
    """Fetches PR metadata and raw diff using gh CLI if available, else GitHub REST API with retry."""
    validate_identifier(owner, repo, pr_num)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    # Try gh CLI first
    gh_bin = shutil.which("gh")
    if gh_bin:
        try:
            meta_res = subprocess.run(
                [gh_bin, "pr", "view", str(pr_num), "--repo", f"{owner}/{repo}", "--json", "title,author,baseRefName,headRefName,body"],
                capture_output=True, text=True, check=True
            )
            meta = json.loads(meta_res.stdout)
            
            diff_res = subprocess.run(
                [gh_bin, "pr", "diff", str(pr_num), "--repo", f"{owner}/{repo}"],
                capture_output=True, text=True, check=True
            )
            diff = diff_res.stdout
            return {
                "title": meta.get("title", ""),
                "author": meta.get("author", {}).get("login", "unknown"),
                "base_ref": meta.get("baseRefName", "main"),
                "head_ref": meta.get("headRefName", "branch"),
                "description": meta.get("body", "") or "No description provided."
            }, diff
        except Exception:
            # Fall back to REST API
            pass

    # GitHub REST API Fallback
    headers = {
        "User-Agent": "Claude-Code-PR-Reviewer/1.3",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(api_url, headers=headers)
    status, raw_json, _ = execute_with_retry(req)
    pr_data = json.loads(raw_json.decode("utf-8"))

    # Fetch diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff_req = urllib.request.Request(api_url, headers=diff_headers)
    _, raw_diff, _ = execute_with_retry(diff_req)
    diff_text = raw_diff.decode("utf-8", errors="replace")

    # Fetch paginated file list for completeness audit
    changed_files = get_paginated_changed_files(owner, repo, pr_num, headers)

    metadata = {
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login", "unknown") if pr_data.get("user") else "unknown",
        "base_ref": pr_data.get("base", {}).get("ref", "main") if pr_data.get("base") else "main",
        "head_ref": pr_data.get("head", {}).get("ref", "branch") if pr_data.get("head") else "branch",
        "description": pr_data.get("body") or "No description provided.",
        "changed_files": changed_files
    }
    return metadata, diff_text

def truncate_diff_if_needed(diff: str, max_chars: int = 45000, changed_files: List[str] = None) -> Tuple[str, str]:
    """Truncates very large diffs gracefully while preserving file headers and providing clear notice."""
    if len(diff) <= max_chars:
        return diff, ""
    
    lines = diff.splitlines()
    truncated_lines = []
    current_chars = 0
    modified_files = set(changed_files or [])
    
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                modified_files.add(parts[2].replace("a/", ""))
        if current_chars + len(line) + 1 > max_chars:
            truncated_lines.append(f"\n... [Diff truncated due to size limit ({max_chars} chars). Evaluated initial files.] ...")
            break
        truncated_lines.append(line)
        current_chars += len(line) + 1
        
    all_files_str = ', '.join(list(modified_files)[:15])
    trunc_note = f"\n⚠️ [NOTE: The complete diff exceeded {max_chars} chars and was truncated. Full changed file list ({len(modified_files)} files): {all_files_str}]\n"
    return "\n".join(truncated_lines), trunc_note

def run_claude_review(prompt: str, lane_id: Optional[int] = None, model: str = "claude-3-5-sonnet-20241022") -> str:
    """
    Executes Claude review via:
    1. Local Lane Manager (if lane_id is set or lane module available)
    2. Local Gateway (http://127.0.0.1:8000/v1/messages)
    3. Anthropic API endpoint
    4. Official Claude CLI ('claude -p')
    """
    # 1. Local Lane Manager
    if lane_id is not None:
        try:
            for p in ["/Users/eiden/hansong", str(Path.cwd()), str(Path.cwd().parent)]:
                if p not in sys.path:
                    sys.path.insert(0, p)
            from bounty.lane_manager import execute_lane
            res = execute_lane(lane_id, prompt, model="sonnet", timeout=180)
            if res.get("success") and res.get("reply"):
                return res["reply"].strip()
        except Exception:
            pass

    # 2. Local Gateway / Anthropic API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    api_base = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("ANTHROPIC_API_BASE")
    
    if not api_base:
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    api_base = "http://127.0.0.1:8000"
        except Exception:
            pass

    if api_base:
        safe_base = validate_api_base(api_base)
        url = f"{safe_base.rstrip('/')}/v1/messages"
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        if api_key:
            headers["x-api-key"] = api_key
        if "127.0.0.1" in safe_base or "localhost" in safe_base:
            headers["x-si-mode"] = "local"

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            status, raw_resp, _ = execute_with_retry(req, max_retries=2, timeout=120)
            data = json.loads(raw_resp.decode("utf-8"))
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block.get("text", "").strip()
        except Exception:
            pass

    # 3. Direct Claude CLI fallback
    claude_cmd = shutil.which("claude") or "/opt/homebrew/bin/claude"
    if claude_cmd and os.path.exists(claude_cmd):
        cmd = [
            claude_cmd,
            "-p", prompt,
            "--no-session-persistence",
            "--dangerously-skip-permissions"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()

    raise RuntimeError("Failed to invoke Claude review: No active Claude CLI, local lane, or API endpoint available.")

def post_comment_to_pr(owner: str, repo: str, pr_num: int, comment_body: str) -> bool:
    """Posts review comment back to GitHub PR with retry and token protection."""
    validate_identifier(owner, repo, pr_num)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    # Try gh CLI
    gh_bin = shutil.which("gh")
    if gh_bin:
        try:
            res = subprocess.run(
                [gh_bin, "pr", "comment", str(pr_num), "--repo", f"{owner}/{repo}", "--body", comment_body],
                check=True, capture_output=True, text=True
            )
            return True
        except Exception as e:
            pass

    # Fallback to GitHub REST API with retry
    if token:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
        headers = {
            "User-Agent": "Claude-Code-PR-Reviewer/1.3",
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        data = json.dumps({"body": comment_body}).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers=headers)
        try:
            status, raw_resp, _ = execute_with_retry(req, max_retries=3, timeout=30)
            return status in (200, 201)
        except Exception as e:
            print(f"[!] Warning: Failed to post comment via API: {sanitize_error(str(e))}", file=sys.stderr)
            return False

    return False

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Reviewer Sub-Agent — Analyzes PR diffs and outputs structured Markdown reviews."
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123) or identifier")
    parser.add_argument("--post", action="store_true", help="Post review comment directly back to the GitHub PR")
    parser.add_argument("--lane", type=int, default=None, help="ComputeJuicer / Multi-Lane account ID to execute on (e.g. 1)")
    parser.add_argument("--output", "-o", help="Optional filepath to save the review markdown report")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Claude model name")
    args = parser.parse_args()

    try:
        owner, repo, pr_num = parse_pr_identifier(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Fetching PR details for {owner}/{repo}#{pr_num}...", file=sys.stderr)
    try:
        meta, diff = get_pr_metadata_and_diff(owner, repo, pr_num)
    except Exception as e:
        print(f"Error fetching PR data: {sanitize_error(str(e))}", file=sys.stderr)
        sys.exit(1)

    if not diff.strip():
        print("Error: PR diff is empty or cannot be retrieved.", file=sys.stderr)
        sys.exit(1)

    clean_diff, trunc_note = truncate_diff_if_needed(diff, changed_files=meta.get("changed_files"))
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        title=meta["title"],
        author=meta["author"],
        base_ref=meta["base_ref"],
        head_ref=meta["head_ref"],
        description=meta["description"],
        diff=clean_diff,
        truncation_note=trunc_note
    )

    print(f"[*] Analyzing PR diff with Claude (Lane: {args.lane if args.lane is not None else 'Default'})...", file=sys.stderr)
    try:
        review = run_claude_review(prompt, lane_id=args.lane, model=args.model)
    except Exception as e:
        print(f"Error during review generation: {sanitize_error(str(e))}", file=sys.stderr)
        sys.exit(1)

    # Output to stdout
    print(review)

    # Optional file output
    if args.output:
        try:
            out_path = Path(args.output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(review, encoding="utf-8")
            print(f"[+] Review saved to {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"[!] Warning: Could not write output file: {sanitize_error(str(e))}", file=sys.stderr)

    # Optional PR comment posting
    if args.post:
        print(f"[*] Posting review comment to {owner}/{repo}#{pr_num}...", file=sys.stderr)
        if post_comment_to_pr(owner, repo, pr_num, review):
            print(f"[+] Successfully posted review to PR #{pr_num}!", file=sys.stderr)
        else:
            print("[!] Could not post comment. Check GITHUB_TOKEN permissions or network connectivity.", file=sys.stderr)

if __name__ == "__main__":
    main()
