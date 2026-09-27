#!/usr/bin/env bash
#
# generate-changelog.sh
# Génère un CHANGELOG.md structuré depuis l'historique git.
# Utilisation : bash generate-changelog.sh [--since-tag <tag>] [--output <fichier>]
#

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
UNTIL_REF="HEAD"

# Parse les arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since-tag)
      SINCE_TAG="$2"
      shift 2
      ;;
    --since)
      SINCE_TAG="$2"
      shift 2
      ;;
    --until)
      UNTIL_REF="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash generate-changelog.sh [--since-tag <tag>] [--until <ref>] [--output <file>]"
      exit 0
      ;;
    *)
      echo "Argument inconnu: $1"
      exit 1
      ;;
  esac
done

# Vérifie qu'on est dans un repo git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Erreur : pas dans un dépôt git." >&2
  exit 1
fi

# Détermine le dernier tag si non spécifié
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..${UNTIL_REF}"
  HEADER="# Changelog\n\n## Changes since ${SINCE_TAG}\n"
else
  RANGE="${UNTIL_REF}"
  HEADER="# Changelog\n\n## All changes\n"
fi

# Récupère les commits (hors merge commits) : hash + message sur une ligne
COMMITS=$(git log "$RANGE" --no-merges --pretty=format:"%s" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "Aucun commit trouvé dans la plage ${RANGE}."
  exit 0
fi

# Fonction de nettoyage du message : retire le prefix conventionnel
clean_message() {
  local msg="$1"
  # Retire les prefixes type feat:, fix:, feat(scope):, etc.
  echo "$msg" | sed -E 's/^[a-z]+(\([^)]+\))?!?:[[:space:]]*//'
}

# Extrait le prefix du commit
get_prefix() {
  local msg="$1"
  echo "$msg" | sed -E 's/^([a-z]+)(\([^)]+\))?!?:.*/\1/' | tr '[:upper:]' '[:lower:]'
}

# Catégorise le prefix
categorize() {
  local prefix="$1"
  case "$prefix" in
    feat|feature|add|new|introduce|implement)
      echo "Added"
      ;;
    fix|bugfix|hotfix|repair|correct|resolve)
      echo "Fixed"
      ;;
    change|update|refactor|perf|improve|enhance|modify|style|test|chore|build|ci)
      echo "Changed"
      ;;
    remove|delete|drop|revert|deprecate)
      echo "Removed"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

# Tableaux par catégorie
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Lit les commits ligne par ligne
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  prefix=$(get_prefix "$line")
  category=$(categorize "$prefix")
  clean=$(clean_message "$line")
  
  case "$category" in
    Added) ADDED+=("$clean") ;;
    Fixed) FIXED+=("$clean") ;;
    Changed) CHANGED+=("$clean") ;;
    Removed) REMOVED+=("$clean") ;;
  esac
done <<< "$COMMITS"

# Génère le CHANGELOG
{
  echo -e "$HEADER"
  echo ""
  
  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for item in "${ADDED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
  
  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for item in "${FIXED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
  
  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for item in "${CHANGED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
  
  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for item in "${REMOVED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "✅ Changelog généré : $OUTPUT_FILE"
