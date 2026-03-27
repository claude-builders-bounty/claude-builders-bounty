# PR Draft: Implement Structured CHANGELOG Generator (#1)

## Summary
Этот PR добавляет автономную утилиту для генерации структурированного CHANGELOG из истории коммитов репозитория.

## Changes
- **[NEW] src/main.py**: Основная логика парсинга `git log` и рендеринга Markdown.
- **[NEW] knowledge/**: Полная база знаний проекта (Tech Spec, Context, Forensic Protocol).
- **[NEW] GEMINI.md**: Манифест юнита для поддержки агентами.

## Verification
- Протестировано на локальных репозиториях: корректно группирует `feat`, `fix`, `docs`.
- Поддержка `Conventional Commits` подтверждена.
- Дифф: **+XXX -0** (Green Diff).

## Payment Information
- **Wallet**: `6eUdVwsPArTxwVqEARYGCh4S2qwW2zCs7jSEDRpxydnv` (SOL)
- **Token**: USDC
