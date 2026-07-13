# Weekly GitHub Dev Summary with n8n + Claude

## Descripción
Workflow en n8n que genera un resumen semanal de actividad en GitHub usando la API de Claude.

## Requisitos
- n8n (self-hosted o cloud)
- API Key de Anthropic (Claude)
- Webhook de Discord o Slack

## Instalación
1. Importa el archivo weekly_summary.json en n8n.
2. Configura las credenciales:
   - GitHub API (token)
   - Anthropic API Key
   - Discord Webhook URL
3. Ajusta el repositorio a monitorear.

## Uso
El workflow se ejecuta automáticamente cada semana (viernes 5pm).

## Personalización
- Modifica el intervalo en el nodo Schedule Trigger.
- Cambia el canal de Discord en el nodo Send to Discord.
