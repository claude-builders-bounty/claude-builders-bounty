"""Core review orchestrator."""

from .github_client import parse_pr_url, get_pr_diff, get_pr_meta
from .llm_client import review_diff

def review_pr(pr_url, token=None, model="gemma4:e4b"):
    owner, repo, num = parse_pr_url(pr_url)
    meta = get_pr_meta(owner, repo, num, token)
    diff = get_pr_diff(owner, repo, num, token)
    result = review_diff(diff, meta, model=model)
    result["pr_url"] = pr_url
    result["pr_number"] = num
    result["pr_title"] = meta.get("title", "")
    result["pr_author"] = meta.get("author", "")
    return format_markdown(result)

def format_markdown(result):
    lines = []
    lines.append(f"## Claude Code PR Review")
    lines.append(f"> PR #{result['pr_number']}: {result['pr_title']} by @{result.get('pr_author','unknown')}")
    lines.append(f"> Backend: {result.get('backend','unknown')} | Confidence: {result.get('confidence','Medium')}")
    lines.append("")
    lines.append("### Summary")
    lines.append(result.get("summary", "No summary generated."))
    lines.append("")
    lines.append("### Risks")
    for r in result.get("risks", []):
        lines.append(f"- {r}")
    if not result.get("risks"):
        lines.append("- None identified")
    lines.append("")
    lines.append("### Suggestions")
    for s in result.get("suggestions", []):
        lines.append(f"- {s}")
    if not result.get("suggestions"):
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)
