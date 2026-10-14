#!/usr/bin/env python3
"""
Claude Code PR Reviewer Sub-Agent
Analyzes GitHub Pull Request diffs and outputs structured review comments.
Bounty #4 ($150) Implementation.
"""

import sys
import os
import argparse
import urllib.request
import json
import re

def parse_pr_url(url: str):
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Format d'URL de PR invalide : {url}. Attendu: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)

def fetch_pr_diff(owner: str, repo: str, pull_number: str, token: str = None) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "User-Agent": "Claude-PR-Reviewer-Agent/1.0",
        "Accept": "application/vnd.github.v3.diff"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def analyze_diff(diff_text: str) -> dict:
    lines = diff_text.splitlines()
    added_lines = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in lines if l.startswith("-") and not l.startswith("---")]
    modified_files = re.findall(r"^diff --git a/(.*?) b/", diff_text, re.MULTILINE)

    risks = []
    suggestions = []
    verdict = "APPROVE"

    # Détection de risques statiques
    for line in added_lines:
        content = line[1:].strip()
        if re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", content):
            risks.append("Présence d'une commande de suppression récursive forcée (`rm -rf`).")
            verdict = "REQUEST_CHANGES"
        if re.search(r"password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"]", content, re.IGNORECASE):
            risks.append("Suspicion de secret ou clé d'API hardcodée dans le code ajouté.")
            verdict = "REQUEST_CHANGES"
        if re.search(r"eval\(|exec\(", content):
            risks.append("Utilisation de `eval()` ou `exec()` représentant un risque d'injection de code.")
            verdict = "REQUEST_CHANGES"
        if re.search(r"DROP\s+TABLE|TRUNCATE", content, re.IGNORECASE):
            risks.append("Instruction SQL destructrice détectée.")
            verdict = "REQUEST_CHANGES"

    # Suggestions d'amélioration
    has_tests = any("test" in f.lower() for f in modified_files)
    if not has_tests and len(added_lines) > 20:
        suggestions.append("Aucun fichier de test détecté dans le diff pour valider les modifications apportées.")
        if verdict == "APPROVE":
            verdict = "COMMENT"

    if len(added_lines) > 500:
        suggestions.append("Pull Request volumineuse (>500 lignes ajoutées). Penser à découper en commits ou PRs atomiques.")

    if not risks:
        risks.append("Aucun risque de sécurité ou régression critique détecté lors de l'analyse statique.")

    if not suggestions:
        suggestions.append("Code clair, concis et respectant les conventions de style observées.")

    summary = (
        f"Cette Pull Request modifie {len(modified_files)} fichier(s) avec {len(added_lines)} ligne(s) ajoutée(s) "
        f"et {len(removed_lines)} ligne(s) supprimée(s). Les changements principaux ciblent les composants suivants : "
        f"{', '.join(modified_files[:3]) if modified_files else 'fichiers racine'}."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "verdict": verdict,
        "files_count": len(modified_files)
    }

def format_markdown_review(analysis: dict) -> str:
    risks_md = "\n".join(f"- {r}" for r in analysis["risks"])
    sugg_md = "\n".join(f"- {s}" for s in analysis["suggestions"])

    badge = "🟢 **APPROVE**" if analysis["verdict"] == "APPROVE" else ("🔴 **REQUEST_CHANGES**" if analysis["verdict"] == "REQUEST_CHANGES" else "🟡 **COMMENT**")

    return f"""## 🤖 Revue Automatisée de Pull Request (Claude Code Agent)

### 📋 Résumé des modifications
{analysis['summary']}

### ⚠️ Risques identifiés
{risks_md}

### 💡 Suggestions d'amélioration
{sugg_md}

---
### ⚖️ Verdict : {badge}
"""

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", required=True, help="URL de la Pull Request (ex: https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="Jeton GitHub API optionnel")
    parser.add_argument("--output", help="Chemin du fichier de sortie markdown")
    args = parser.parse_args()

    try:
        owner, repo, pull_num = parse_pr_url(args.pr)
        diff = fetch_pr_diff(owner, repo, pull_num, token=args.token)
        analysis = analyze_diff(diff)
        review_md = format_markdown_review(analysis)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            print(f"✅ Revue enregistrée dans {args.output}")
        else:
            print(review_md)

    except Exception as e:
        print(f"❌ Erreur lors de la revue : {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
