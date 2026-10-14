#!/usr/bin/env bash
# Test suite for the generate-changelog skill.
# Builds throwaway repositories and checks the generated sections.
# Run: bash test/run-tests.sh
set -u

SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/changelog.sh"
ROOT="$(mktemp -d)"
pass=0
fail=0

ok()   { printf '  ok    %s\n' "$1"; pass=$((pass + 1)); }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail + 1)); }
check(){ if printf '%s' "$2" | grep -q -- "$3"; then ok "$1"; else bad "$1"; fi; }
check_not(){ if printf '%s' "$2" | grep -q -- "$3"; then bad "$1"; else ok "$1"; fi; }

make_repo() {
  git init -q "$1" && cd "$1" &&
  git config user.email test@example.com && git config user.name Test &&
  git config commit.gpgsign false
}

commit() { # commit <message> <n>
  echo "$2" > "file$2.txt"
  GIT_AUTHOR_DATE="2026-01-0$2T10:00:00Z" GIT_COMMITTER_DATE="2026-01-0$2T10:00:00Z" \
    git add -A && GIT_AUTHOR_DATE="2026-01-0$2T10:00:00Z" GIT_COMMITTER_DATE="2026-01-0$2T10:00:00Z" \
    git commit -q -m "$1"
}

echo "== repo con tag previo =="
REPO="$ROOT/repo-tag"
make_repo "$REPO" >/dev/null
commit "feat: initial release" 1
git tag v1.0.0
commit "feat(api): add pagination" 2
commit "fix: handle empty response" 3
commit "refactor: split the parser" 4
commit "chore: bump dependencies" 5
commit "docs: fix typos" 6
commit "feat!: drop Node 16 support" 7
commit "remove: legacy endpoint" 8
commit "Bump eslint from 9.39.1 to 9.39.2" 9

OUT="$(bash "$SCRIPT" --stdout 2>/dev/null)"
printf '%s\n' "$OUT" | sed 's/^/      /'

echo
echo "== contenido de la seccion =="
check     "incluye ### Added"            "$OUT" "### Added"
check     "incluye ### Fixed"            "$OUT" "### Fixed"
check     "incluye ### Changed"          "$OUT" "### Changed"
check     "incluye ### Removed"          "$OUT" "### Removed"
check     "incluye ### Breaking changes" "$OUT" "### Breaking changes"
check     "aplica el scope en negrita"   "$OUT" '\*\*api:\*\*'
check     "respeta el tag de origen"     "$OUT" 'Changes since `v1.0.0`'
check_not "omite chore sin --all"        "$OUT" "Bump dependencies"
check_not "omite docs sin --all"         "$OUT" "Fix typos"
check_not "omite bumps sin --all"        "$OUT" "Bump eslint"
check_not "omite el commit del tag"      "$OUT" "Initial release"
check_not "omite el prefijo feat:"       "$OUT" "feat(api):"
check     "lista el breaking en su bloque" "$OUT" "Drop Node 16 support"
check     "categoriza remove:"           "$OUT" "Legacy endpoint"

OUT_ALL="$(bash "$SCRIPT" --stdout --all 2>/dev/null)"
check "con --all incluye chore" "$OUT_ALL" "Bump dependencies"
check "con --all incluye docs"  "$OUT_ALL" "Fix typos"
check "con --all incluye bumps" "$OUT_ALL" "Bump eslint"

OUT_HASH="$(bash "$SCRIPT" --stdout --hashes 2>/dev/null)"
if printf '%s' "$OUT_HASH" | grep -Eq '\(`[0-9a-f]{7,}`\)'; then ok "con --hashes añade el hash"; else bad "con --hashes añade el hash"; fi

# Una entrada por linea: la sustitucion de comandos se come el salto final, asi que
# sin separador explicito dos entradas quedan pegadas en la misma linea.
LINES="$(printf '%s\n' "$OUT" | grep -c '^- ')"
if [ "$LINES" = "6" ]; then ok "una entrada por linea (6 lineas)"; else bad "una entrada por linea (encontradas $LINES, esperadas 6)"; fi
GLUED="$(printf '%s\n' "$OUT" | grep -Ec '^- .+- ' || true)"
if [ "$GLUED" = "0" ]; then ok "sin entradas pegadas en la misma linea"; else bad "hay $GLUED lineas con dos entradas pegadas"; fi

echo
echo "== escritura del archivo y orden =="
bash "$SCRIPT" 1.1.0 >/dev/null 2>&1
[ -f CHANGELOG.md ] && ok "crea CHANGELOG.md" || bad "crea CHANGELOG.md"
FILE="$(cat CHANGELOG.md 2>/dev/null || true)"
check "escribe la cabecera Keep a Changelog" "$FILE" "Keep a Changelog"
check "usa la version pedida"                "$FILE" "## \[1.1.0\]"

commit "fix: correct the parser edge case" 10
bash "$SCRIPT" 1.2.0 >/dev/null 2>&1
FILE="$(cat CHANGELOG.md)"
FIRST="$(grep -n '^## \[' CHANGELOG.md | head -1)"
SECOND="$(grep -n '^## \[' CHANGELOG.md | sed -n '2p')"
check "inserta la version nueva arriba" "$FILE" "## \[1.2.0\]"
if printf '%s\n' "$FIRST" | grep -q '1.2.0' && printf '%s\n' "$SECOND" | grep -q '1.1.0'; then
  ok "mantiene el orden mas nuevo primero"
else
  bad "mantiene el orden mas nuevo primero ($FIRST / $SECOND)"
fi

echo
echo "== repo sin tags =="
REPO2="$ROOT/repo-sin-tag"
make_repo "$REPO2" >/dev/null
commit "feat: first feature" 1
commit "fix: first bug" 2
OUT2="$(bash "$SCRIPT" --stdout 2>/dev/null)"
check     "funciona sin tags (Added)"        "$OUT2" "### Added"
check     "funciona sin tags (Fixed)"        "$OUT2" "### Fixed"
check_not "sin tag no anuncia rango"         "$OUT2" "Changes since"

echo
echo "== caso borde: rango vacio =="
OUT3="$(bash "$SCRIPT" --stdout --since HEAD 2>/dev/null)"
check "avisa cuando no hay cambios" "$OUT3" "No documentable changes"

echo
echo "== --help =="
OUT4="$(bash "$SCRIPT" --help 2>&1)"
check "--help muestra el uso" "$OUT4" "Usage:"

cd / && rm -rf "$ROOT"
echo
echo "RESULTADO: $pass pasaron, $fail fallaron"
[ "$fail" = "0" ]
