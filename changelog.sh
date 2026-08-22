#!/usr/bin/env bash
# changelog.sh — генерирует структурированный CHANGELOG.md из git-истории.
# Берёт коммиты с последнего тега (или с начала истории, если тегов нет),
# категоризирует по Conventional Commits и собирает CHANGELOG.md в формате Keep a Changelog.
#
# Использование:
#   bash changelog.sh                # записать в CHANGELOG.md
#   bash changelog.sh --stdout       # вывести в stdout, не писать файл
#   bash changelog.sh --since v1.2.3 # считать с конкретного тега
#   bash changelog.sh --help

set -euo pipefail

# ---------- Конфигурация ----------
# Категории: ключевое слово коммита -> заголовок секции
declare -A CATEGORY_TITLES=(
  [Added]="Added"
  [Fixed]="Fixed"
  [Changed]="Changed"
  [Removed]="Removed"
  [Security]="Security"
  [Deprecated]="Deprecated"
)
# Маппинг типов Conventional Commits на категории (ключи без скобок)
declare -A TYPE_MAP=(
  [feat]=Added
  [feature]=Added
  [fix]=Fixed
  [bugfix]=Fixed
  [hotfix]=Fixed
  [refactor]=Changed
  [perf]=Changed
  [performance]=Changed
  [style]=Changed
  [chore]=Changed
  [build]=Changed
  [ci]=Changed
  [docs]=Changed
  [test]=Changed
  [tests]=Changed
  [revert]=Removed
  [remove]=Removed
  [delete]=Removed
  [security]=Security
  [deprecate]=Deprecated
  [deprecated]=Deprecated
)

# ---------- Вспомогательные функции ----------
print_help() {
  cat <<'EOF'
changelog.sh — генератор CHANGELOG.md из git-истории

Использование:
  bash changelog.sh                 Сгенерировать CHANGELOG.md в текущей директории
  bash changelog.sh --stdout        Вывести результат в stdout (файл не трогаем)
  bash changelog.sh --since <тег>   Считать коммиты только после указанного тега
  bash changelog.sh --help          Эта справка

Как это работает:
  1. Находит последний git-тег (git describe --tags --abbrev=0).
     Если тегов нет — берёт всю историю.
  2. Собирает коммиты с этого тега до HEAD.
  3. Категоризирует по Conventional Commits
     (feat:, fix:, refactor:, docs:, test:, chore:, perf:, style:, build:, ci:, security:, revert:).
     Коммиты без префикса попадают в "Changed".
  4. Собирает CHANGELOG.md в формате Keep a Changelog:
     - секции Added / Fixed / Changed / Removed / Security / Deprecated
     - ссылка на сравнение тегов (если тег найден)

Примеры:
  bash changelog.sh
  bash changelog.sh --stdout --since v1.0.0
EOF
}

# Парсим аргументы
OUTPUT_FILE="CHANGELOG.md"
TO_STDOUT=0
SINCE_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout) TO_STDOUT=1 ;;
    --since)
      shift
      SINCE_ARG="${1:-}"
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "Неизвестный аргумент: $1 (см. bash changelog.sh --help)" >&2
      exit 1
      ;;
  esac
  shift
done

# ---------- Определяем диапазон коммитов ----------
LAST_TAG=""
RANGE=""

if [[ -n "$SINCE_ARG" ]]; then
  LAST_TAG="$SINCE_ARG"
  RANGE="${LAST_TAG}..HEAD"
elif git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  RANGE="${LAST_TAG}..HEAD"
else
  # Тегов нет — берём всю историю
  RANGE="HEAD"
fi

# ---------- Собираем коммиты ----------
# Формат строки: <тип>|<заголовок>
COMMITS=""
if [[ "$RANGE" == "HEAD" ]]; then
  COMMITS="$(git log --pretty=format:'%s' HEAD)"
else
  COMMITS="$(git log --pretty=format:'%s' "$RANGE")"
fi

if [[ -z "$COMMITS" ]]; then
  echo "Нет коммитов в диапазоне${RANGE:+ ($RANGE)}. Нечего записывать." >&2
  exit 0
fi

# ---------- Категоризируем ----------
# Массив вида "Added|заголовок", "Fixed|заголовок", ...
declare -a ENTRIES=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # Убираем merge-коммиты и squash-заголовки
  if [[ "$line" =~ ^(Merge|Revert) ]]; then
    continue
  fi
  # Парсим Conventional Commit: "feat(scope): message"
  # Разбиваем вручную — без регулярок (совместимость с разными bash)
  prefix="${line%%:*}"
  if [[ "$prefix" != "$line" ]]; then
    # есть двоеточие — это conventional commit
    type="${prefix,,}"
    subject="${line#*:}"
    subject="${subject#"${subject%%[![:space:]]*}"}"  # срезаем ведущие пробелы
    # достаём scope: "feat(api)" -> type=feat, scope=api
    scope=""
    if [[ "$type" == *"("* ]]; then
      scope="${type#*(}"
      scope="${scope%)*}"
      type="${type%%(*}"
    fi
    # Capitalize первую букву subject
    subject="$(echo "${subject:0:1}" | tr '[:lower:]' '[:upper:]')${subject:1}"
    cat_key="${TYPE_MAP[$type]:-Changed}"
    if [[ -n "$scope" ]]; then
      subject="${subject} (${scope})"
    fi
  else
    # Обычный коммит без типа — пробуем угадать по глаголу
    subject="${line}"
    subject="$(echo "${subject:0:1}" | tr '[:lower:]' '[:upper:]')${subject:1}"
    lower_line="${line,,}"
    if [[ "$lower_line" =~ ^(fix|fixed|repair|resolve|solves?|correct|hotfix) ]]; then
      cat_key="Fixed"
    elif [[ "$lower_line" =~ ^(add|added|implement|introduce|support|new|create|feature) ]]; then
      cat_key="Added"
    elif [[ "$lower_line" =~ ^(remov|delet|drop|deprecat) ]]; then
      cat_key="Removed"
    else
      cat_key="Changed"
    fi
  fi
  ENTRIES+=("${cat_key}|${subject}")
done <<< "$COMMITS"

# ---------- Собираем Markdown ----------
DATE="$(date +%Y-%m-%d)"
VERSION_HEADER="Unreleased"
if [[ -n "$LAST_TAG" ]]; then
  # Пробуем угадать следующую версию: tag вида v1.2.3 -> v1.2.4
  if [[ "$LAST_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    VERSION_HEADER="v${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))"
  else
    VERSION_HEADER="${LAST_TAG}"
  fi
fi

# Собираем секции в фиксированном порядке
ORDER=(Added Fixed Changed Removed Security Deprecated)
OUT=""
OUT+="# Changelog\n\n"
OUT+="## [${VERSION_HEADER}] - ${DATE}\n\n"

SECTION_OPENED=0
for cat in "${ORDER[@]}"; do
  # Собираем записи этой категории в порядке появления
  items=()
  for entry in "${ENTRIES[@]}"; do
    if [[ "${entry%%|*}" == "$cat" ]]; then
      items+=("${entry#*|}")
    fi
  done
  if [[ ${#items[@]} -gt 0 ]]; then
    OUT+="### ${CATEGORY_TITLES[$cat]}\n\n"
    for item in "${items[@]}"; do
      OUT+="- ${item}\n"
    done
    OUT+="\n"
    SECTION_OPENED=1
  fi
done

if [[ $SECTION_OPENED -eq 0 ]]; then
  OUT+="_Нет изменений в этом диапазоне._\n"
fi

# Ссылка на сравнение тегов (если есть предыдущий тег)
if [[ -n "$LAST_TAG" && "$LAST_TAG" != "$SINCE_ARG" ]]; then
  REMOTE_URL="$(git config --get remote.origin.url 2>/dev/null || true)"
  if [[ -n "$REMOTE_URL" && "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    REPO_OWNER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    OUT+="[Сравнение с ${LAST_TAG}](https://github.com/${REPO_OWNER}/${REPO_NAME}/compare/${LAST_TAG}...HEAD)\n"
  fi
fi

# ---------- Вывод ----------
if [[ $TO_STDOUT -eq 1 ]]; then
  printf "%b" "$OUT"
else
  printf "%b" "$OUT" > "$OUTPUT_FILE"
  echo "Готово: ${OUTPUT_FILE} (${#ENTRIES[@]} коммитов, диапазон: ${RANGE})"
fi
