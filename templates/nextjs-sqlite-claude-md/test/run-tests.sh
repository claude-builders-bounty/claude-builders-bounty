#!/usr/bin/env bash
# Verifies the template as a whole: the document must match the fixture, and the
# validator must actually catch drift (a validator that never fails proves nothing).
#
# Needs only node; the fixture's dependencies are not required.
# Run: bash test/run-tests.sh
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
pass=0
fail=0

ok()  { printf '  ok    %s\n' "$1"; pass=$((pass + 1)); }
bad() { printf '  FAIL  %s\n' "$1"; fail=$((fail + 1)); }

echo "== el documento y el proyecto estan de acuerdo =="
SALIDA="$(node "$ROOT/check.mjs" "$ROOT/CLAUDE.md" "$ROOT/fixture" 2>&1)"
CODIGO=$?
if [ "$CODIGO" = "0" ]; then ok "check.mjs sale 0 con el documento real"; else bad "check.mjs fallo con el documento real"; fi
if printf '%s' "$SALIDA" | grep -q "0 fallos"; then ok "informa 0 fallos"; else bad "no informa 0 fallos"; fi
RUTAS="$(printf '%s' "$SALIDA" | grep -c '^  ok    existe:')"
if [ "$RUTAS" -ge 5 ]; then ok "verifica rutas concretas ($RUTAS)"; else bad "solo verifico $RUTAS rutas"; fi
COMANDOS="$(printf '%s' "$SALIDA" | grep -c 'existe en package.json')"
if [ "$COMANDOS" -ge 8 ]; then ok "verifica los comandos npm ($COMANDOS)"; else bad "solo verifico $COMANDOS comandos"; fi

echo
echo "== el validador detecta desincronizacion =="
# 1. Un comando documentado que no existe en package.json.
sed 's|^## Dev commands|## Dev commands\n\nTambien corre `npm run no-existe-este-script`.|' "$ROOT/CLAUDE.md" > "$TMP/con-comando-falso.md"
if ! node "$ROOT/check.mjs" "$TMP/con-comando-falso.md" "$ROOT/fixture" >/dev/null 2>&1; then
  ok "detecta un npm run documentado que no existe"
else
  bad "no detecto el comando inexistente"
fi

# 2. Una ruta citada que no existe.
sed 's|^## Dev commands|## Dev commands\n\nVer `lib/queries/clientes.ts` para mas detalle.|' "$ROOT/CLAUDE.md" > "$TMP/con-ruta-falsa.md"
if ! node "$ROOT/check.mjs" "$TMP/con-ruta-falsa.md" "$ROOT/fixture" >/dev/null 2>&1; then
  ok "detecta una ruta citada que no existe"
else
  bad "no detecto la ruta inexistente"
fi

# 3. Una variable de entorno documentada que falta en .env.example.
python3 - "$ROOT/CLAUDE.md" "$TMP/con-env-falso.md" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read().replace('NODE_ENV=development', 'NODE_ENV=development\nSTRIPE_SECRET=sk_test')
open(dst, 'w', encoding='utf-8').write(text)
PY
if [ -f "$TMP/con-env-falso.md" ]; then
  if ! node "$ROOT/check.mjs" "$TMP/con-env-falso.md" "$ROOT/fixture" >/dev/null 2>&1; then
    ok "detecta una variable de entorno fuera de .env.example"
  else
    bad "no detecto la variable ausente"
  fi
fi

# 4. Un documento sin las secciones obligatorias.
printf '# CLAUDE.md\n\nEsto no cubre nada de lo pedido.\n' > "$TMP/vacio.md"
if ! node "$ROOT/check.mjs" "$TMP/vacio.md" "$ROOT/fixture" >/dev/null 2>&1; then
  ok "detecta un documento sin las secciones obligatorias"
else
  bad "acepto un documento vacio"
fi

echo
echo "== las secciones que pide el bounty estan presentes =="
for seccion in "Stack and versions" "Folder structure" "Dev commands" "SQL and migration conventions" "Component patterns" "What we don't do"; do
  if grep -qi "^## $seccion" "$ROOT/CLAUDE.md"; then ok "seccion: $seccion"; else bad "falta la seccion: $seccion"; fi
done

rm -rf "$TMP"
echo
echo "RESULTADO: $pass pasaron, $fail fallaron"
[ "$fail" = "0" ]
