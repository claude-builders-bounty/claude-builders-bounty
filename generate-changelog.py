#!/usr/bin/env python3
"""
generate-changelog.py
Génère un CHANGELOG.md structuré depuis l'historique git.
Utilisation : python generate-changelog.py [--since-tag TAG] [--output FILE]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Force UTF-8 pour Windows
sys.stdout.reconfigure(encoding='utf-8')


def run_git(args):
    """Exécute une commande git et retourne la sortie."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.strip(), result.returncode


def get_last_tag():
    """Retourne le dernier tag git, ou None."""
    output, code = run_git(["describe", "--tags", "--abbrev=0"])
    return output if code == 0 else None


def get_commits(since_tag=None, until_ref="HEAD"):
    """Récupère les commits depuis le dernier tag (ou depuis le début)."""
    if since_tag:
        commit_range = f"{since_tag}..{until_ref}"
    else:
        commit_range = until_ref
    
    output, code = run_git([
        "log", commit_range,
        "--no-merges",
        "--pretty=format:%s"
    ])
    
    if code != 0:
        print(f"Erreur lors de la récupération des commits pour {commit_range}", file=sys.stderr)
        return []
    
    return [line.strip() for line in output.split("\n") if line.strip()]


def parse_prefix(message):
    """Extrait le prefix conventionnel d'un message de commit."""
    match = re.match(r'^([a-z]+)(?:\([^)]+\))?!?:\s*', message, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return ""


def clean_message(message):
    """Retire le prefix conventionnel du message."""
    return re.sub(r'^[a-z]+(?:\([^)]+\))?!?:\s*', '', message, flags=re.IGNORECASE).strip()


def categorize(prefix):
    """Catégorise un prefix en Added / Fixed / Changed / Removed."""
    added = {'feat', 'feature', 'add', 'new', 'introduce', 'implement'}
    fixed = {'fix', 'bugfix', 'hotfix', 'repair', 'correct', 'resolve'}
    changed = {'change', 'update', 'refactor', 'perf', 'improve', 'enhance', 'modify', 'style', 'test', 'chore', 'build', 'ci'}
    removed = {'remove', 'delete', 'drop', 'revert', 'deprecate'}
    
    if prefix in added:
        return "Added"
    elif prefix in fixed:
        return "Fixed"
    elif prefix in removed:
        return "Removed"
    else:
        return "Changed"


def generate_changelog(commits, since_tag=None):
    """Génère le contenu du changelog."""
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for commit in commits:
        prefix = parse_prefix(commit)
        category = categorize(prefix)
        clean = clean_message(commit)
        categories[category].append(clean)
    
    if since_tag:
        header = f"# Changelog\n\n## Changes since {since_tag}\n"
    else:
        header = "# Changelog\n\n## All changes\n"
    
    lines = [header, ""]
    
    for category in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[category]
        if items:
            lines.append(f"### {category}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Génère un CHANGELOG.md structuré depuis l'historique git."
    )
    parser.add_argument(
        "--since-tag",
        help="Tag de départ (par défaut : dernier tag)"
    )
    parser.add_argument(
        "--since",
        dest="since_tag",
        help="Alias de --since-tag"
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help="Référence de fin (par défaut : HEAD)"
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Fichier de sortie (par défaut : CHANGELOG.md)"
    )
    
    args = parser.parse_args()
    
    # Vérifie qu'on est dans un repo git
    _, code = run_git(["rev-parse", "--git-dir"])
    if code != 0:
        print("Erreur : pas dans un dépôt git.", file=sys.stderr)
        sys.exit(1)
    
    since_tag = args.since_tag or get_last_tag()
    commits = get_commits(since_tag, args.until)
    
    if not commits:
        print(f"Aucun commit trouvé depuis {since_tag or 'le début'}.")
        sys.exit(0)
    
    changelog = generate_changelog(commits, since_tag)
    
    output_path = Path(args.output)
    output_path.write_text(changelog, encoding="utf-8")
    
    print(f"✅ Changelog généré : {output_path}")


if __name__ == "__main__":
    main()
