# destructive-command-hook

Un hook `PreToolUse` pequeño y local para Claude Code. Lee el evento JSON de stdin y bloquea, antes de ejecutar, estos casos de alto riesgo:

- `rm -rf` (incluidas las variantes separadas `-r -f`).
- `git push --force` / `git push -f`.
- `DROP TABLE` y `TRUNCATE`.
- `DELETE FROM` cuando la sentencia no tiene `WHERE`.
- En Windows, `Remove-Item -Recurse -Force` y equivalentes comunes.

Cada bloqueo se añade como una línea JSON a `~/.claude/hooks/blocked.log`, con timestamp UTC, comando, ruta del proyecto y regla. El hook devuelve el código de salida `2` y una explicación clara a Claude Code. Los comandos seguros (incluidos `git status`, `rm archivo`, `DELETE ... WHERE ...` y ejemplos dentro de `echo`) pasan sin salida.

## Instalación (dos comandos)

Desde esta carpeta:

```text
python destructive_command_hook.py --install
python -m unittest -v
```

El primer comando crea o actualiza `~/.claude/settings.json`, conserva la configuración existente y registra el matcher `Bash|PowerShell`. Si se usa una instalación de Python distinta en el entorno de Claude Code, edita el comando guardado en `settings.json` para apuntar a ese intérprete.

## Uso y pruebas

Claude Code invoca el script como comando de hook y le entrega un único evento JSON por stdin. Para una prueba aislada segura:

```powershell
'{"tool_name":"Bash","tool_input":{"command":"rm -rf ./fixture"},"cwd":"C:\\fixture-project"}' | python .\destructive_command_hook.py
```

La prueba anterior solo analiza una cadena: nunca ejecuta `rm`. Las pruebas automatizadas tampoco ejecutan comandos de shell.

También se puede escoger otro archivo de log durante pruebas o integración con `DESTRUCTIVE_HOOK_LOG`. El valor por defecto cumple el bounty: `~/.claude/hooks/blocked.log`.

## Decisiones y límites

La normalización separa operadores compuestos (`;`, `&&`, `||`, `|` y saltos de línea) solo cuando están fuera de comillas, reconoce Bash y formas frecuentes de PowerShell y evita bloquear texto meramente citado en `echo`/`printf`/`Write-Output`. No evalúa shell, no sigue aliases o funciones, no es un parser SQL completo y no pretende ser un sandbox: una defensa real debe combinarlo con permisos mínimos, revisión humana, backups y controles del sistema de archivos. Los wrappers, codificaciones y sintaxis shell exótica pueden requerir reglas adicionales.

## Pendiente de revisión

- Validar la sintaxis exacta de `settings.json` contra la versión de Claude Code usada en cada equipo.
- Añadir casos específicos si el equipo usa aliases, wrappers SQL o shells distintos.
- Decidir una política de rotación si `blocked.log` crece mucho.

Licencia: MIT.
