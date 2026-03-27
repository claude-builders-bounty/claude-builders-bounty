# Error Resolver: Git Changelog

## 🚨 Git Repository Not Found
- **Symptoms**: `fatal: not a git repository (or any of the parent directories): .git`
- **Solution**: Убедитесь, что скрипт запускается внутри или выше папки с `.git`. Используйте `main.py --repo <path>`.

## 🚨 No Tags Found
- **Symptoms**: `CHANGELOG` начинается с "Unreleased" без истории версий.
- **Solution**: Скрипт по умолчанию ищет самый свежий тег. Если тегов нет, он берет всю историю от первого коммита. Создайте тег `git tag v1.0.0` для проверки.

## 🚨 Permission Denied
- **Symptoms**: Ошибка при записи в `CHANGELOG.md`.
- **Solution**: Проверьте права доступа в директории. Используйте `--output /tmp/CHANGELOG.md` для теста.

## 🚨 Regex Mismatch
- **Symptoms**: Все коммиты попадают в секцию `misc`.
- **Solution**: Убедитесь, что ваши коммиты следуют формату: `type: description`. Пример: `feat: add backup system`.
