import subprocess
from review_template import generate_review

def fetch_pr_diff(owner, repo, pr_number):
    try:
        cmd = ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}", "-H", "Accept: application/vnd.github.v3.diff"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to fetch PR diff: {e.stderr}")

def analyze_diff(diff_text):
    risks = []
    improvements = []
    
    security_patterns = {
        "eval(": "Avoid using 'eval()', it poses a critical security risk.",
        "exec(": "Avoid using 'exec()', it poses a critical security risk.",
        "os.system(": "Consider using 'subprocess' instead of 'os.system()' to avoid shell injection.",
        "password =": "Potential hardcoded credential found. Avoid committing secrets.",
        "api_key =": "Potential hardcoded API key found. Use environment variables.",
    }
    
    bug_patterns = {
        "except:": "Bare 'except:' block found. Catch specific exceptions to avoid hiding bugs.",
        "== True": "Avoid '== True' comparisons. Use implicit boolean checks.",
        "== False": "Avoid '== False' comparisons. Use 'not' for boolean checks.",
        "pass": "Empty 'pass' statement found. Ensure this is intentional."
    }
    
    perf_patterns = {
        ".append(": "Consider if a list comprehension could replace '.append()' in loops for better performance."
    }

    added_lines = [line[1:] for line in diff_text.splitlines() if line.startswith('+') and not line.startswith('+++')]
    
    for line in added_lines:
        for pat, msg in security_patterns.items():
            if pat in line and msg not in risks:
                risks.append(msg)
        for pat, msg in bug_patterns.items():
            if pat in line and msg not in improvements:
                improvements.append(msg)
        for pat, msg in perf_patterns.items():
            if pat in line and msg not in improvements:
                improvements.append(msg)
    
    if len(risks) > 0:
        confidence = "High"
    elif len(improvements) > 2:
        confidence = "Medium"
    else:
        confidence = "Low"
        
    if not risks:
        risks.append("No critical security risks identified based on static patterns.")
    if not improvements:
        improvements.append("Code looks clean and follows basic standards. No obvious improvements identified.")
        
    additions = len(added_lines)
    summary = f"This PR introduces approximately {additions} lines of new additions or modifications. "
    summary += "The changes have been statically analyzed for common security flaws, potential bugs, and performance bottlenecks."
    
    return {
        "summary": summary,
        "risks": risks,
        "improvements": improvements,
        "confidence": confidence
    }

def run_review(owner, repo, pr_number):
    diff = fetch_pr_diff(owner, repo, pr_number)
    if not diff.strip():
        return "No changes found in the PR or unable to access the PR."
    analysis = analyze_diff(diff)
    return generate_review(analysis)
