# Versioning Rules

## ОБЯЗАТЕЛЬНО при любых изменениях кода

После завершения задачи, которая изменяет функциональность, **ВСЕГДА** выполняй версионирование:

### Когда бампить версию

| Тип изменения | Bump | Пример |
|---------------|------|--------|
| Баг-фикс | PATCH | 1.2.0 → 1.2.1 |
| Новая фича | MINOR | 1.2.0 → 1.3.0 |
| Breaking change | MAJOR | 1.2.0 → 2.0.0 |
| Только документация | НЕ бампить | - |
| Только комментарии | НЕ бампить | - |

### Что считается новой фичей (MINOR)

- Новый tool в плагине
- Новый API endpoint
- Новый сервис
- CI/CD pipeline
- Новая интеграция
- Значительное улучшение функциональности

### Что считается баг-фиксом (PATCH)

- Исправление ошибок
- Исправление безопасности
- Мелкие улучшения
- Рефакторинг без изменения API

## Процедура релиза

### 1. Обновить файлы версии

```bash
# Файлы для обновления:
VERSION                           # Главный файл версии
aifood-plugin/package.json        # "version": "X.Y.Z"
services/llm-gateway/package.json # "version": "X.Y.Z"
```

### 2. Обновить CHANGELOG.md

Добавить новую секцию **ПЕРЕД** предыдущей версией:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Что добавлено

### Changed
- Что изменено

### Fixed
- Что исправлено

---

## [предыдущая версия]
```

### 3. Обновить VERSIONING.md

Добавить строку в таблицу Version History.

### 4. Обновить .claude/CLAUDE.md

Обновить строку `**Version**: X.Y.Z`

### 5. Git commit и tag

```bash
git add VERSION CHANGELOG.md VERSIONING.md .claude/CLAUDE.md \
        aifood-plugin/package.json services/llm-gateway/package.json

git commit -m "chore: Release vX.Y.Z

### Added/Changed/Fixed
- Краткое описание изменений

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git tag -a vX.Y.Z -m "Release vX.Y.Z - краткое описание"
git push origin main --tags
```

## Автоматизация

Можно использовать скрипт:

```bash
./scripts/bump-version.sh patch  # 1.2.0 → 1.2.1
./scripts/bump-version.sh minor  # 1.2.0 → 1.3.0
./scripts/bump-version.sh major  # 1.2.0 → 2.0.0
```

## Checklist перед завершением задачи

- [ ] Код изменяет функциональность? → Бампить версию
- [ ] VERSION обновлён
- [ ] package.json файлы обновлены
- [ ] CHANGELOG.md обновлён
- [ ] VERSIONING.md обновлён
- [ ] .claude/CLAUDE.md обновлён
- [ ] Git tag создан
- [ ] Push с тегами выполнен

## Ссылки

- [VERSION](../../VERSION) — текущая версия
- [CHANGELOG.md](../../CHANGELOG.md) — история изменений
- [VERSIONING.md](../../VERSIONING.md) — полный гайд
- [bump-version.sh](../../scripts/bump-version.sh) — скрипт автоматизации
