#!/usr/bin/env python3
"""
claude_review.py - Sub-agent CLI for PR Code Review with structured Markdown output
"""

import sys
import os
import re
import json
import argparse
import urllib.request
from urllib.parse import urlparse

def parse_pr_url(url):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 4 and parts[2] in ["pull", "pulls"]:
        return parts[0], parts[1], parts[3]
    raise ValueError(f"URL de PR inválida: {url}. Formato esperado: https://github.com/owner/repo/pull/123")

def fetch_pr_diff(owner, repo, pr_number, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "Claude-Review-Agent"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar diff do PR: {e}")

def analyze_diff(diff_text):
    added_lines = [l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---")]
    files_changed = re.findall(r"diff --git a/(.*?) b/", diff_text)
    
    risks = []
    suggestions = []
    
    # Análise estática de segurança e qualidade
    diff_lower = diff_text.lower()
    if "password" in diff_lower or "secret" in diff_lower or "api_key" in diff_lower or "token" in diff_lower:
        risks.append("Possível exposição ou manipulação de credenciais/chaves de API no diff.")
    if "eval(" in diff_text or "exec(" in diff_text or "os.system(" in diff_text:
        risks.append("Uso de funções de execução dinâmica que podem levar a injeção de comando.")
    if "except:" in diff_text or "except Exception:" in diff_text:
        suggestions.append("Refinar tratamento de exceções para evitar capturar erros silenciosamente.")
    if not any("test" in f.lower() for f in files_changed):
        suggestions.append("Adicionar testes unitários ou de integração para as alterações propostas.")
        
    if not risks:
        risks.append("Nenhum risco de segurança crítico ou blocker detectado na análise estática inicial.")
    if not suggestions:
        suggestions.append("Manter boa cobertura de documentação e validar linting no pipeline de CI.")

    confidence = "High" if len(files_changed) <= 5 else "Medium"
    
    summary = f"O PR modifica {len(files_changed)} arquivo(s), adicionando {len(added_lines)} linha(s) e removendo {len(removed_lines)} linha(s). " \
              f"As alterações concentram-se principalmente em: {', '.join(files_changed[:3])}{'...' if len(files_changed) > 3 else ''}."
              
    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_count": len(files_changed)
    }

def format_review_markdown(analysis):
    md = []
    md.append("## 🤖 Automated PR Review Summary\n")
    md.append(f"**Summary of Changes:**\n{analysis['summary']}\n")
    
    md.append("**Identified Risks:**")
    for r in analysis["risks"]:
        md.append(f"- ⚠️ {r}")
    md.append("")
    
    md.append("**Improvement Suggestions:**")
    for s in analysis["suggestions"]:
        md.append(f"- 💡 {s}")
    md.append("")
    
    md.append(f"**Confidence Score:** `{analysis['confidence']}`")
    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Claude Code Sub-Agent for PR Reviews")
    parser.add_argument("--pr", required=True, help="URL do Pull Request no GitHub (ex: https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Token (opcional para repositórios públicos)")
    parser.add_argument("--output", help="Caminho do arquivo de saída (opcional, imprime no stdout por padrão)")
    
    args = parser.parse_args()
    
    owner, repo, pr_num = parse_pr_url(args.pr)
    diff = fetch_pr_diff(owner, repo, pr_num, args.token)
    analysis = analyze_diff(diff)
    markdown_output = format_review_markdown(analysis)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown_output)
        print(f"Review salvo em {args.output}")
    else:
        print(markdown_output)

if __name__ == "__main__":
    main()
