# AGENTS.md — tgcrm (Telegram Account Orchestrator, локальный деплой)

Self-hosted менеджер Telegram-аккаунтов (Telethon + FastAPI, одна страница UI).
Этот файл — про **наш** деплой и модификации, не про upstream.

## Что где

| Что | Где |
|-----|-----|
| Проект | `/home/golden/Проекты/tgcrm` |
| Виртуальное окружение | `.venv` (Python 3.14) |
| Конфиг и секреты | `.env` (не индексировать, не печатать) |
| Данные (SQLite, логи) | `data/` — `tam.sqlite3`, `service.log`, `errors.log` |
| Сервис | `systemctl --user {status,restart} tgcrm` → `http://127.0.0.1:8848` |
| Юнит | `~/.config/systemd/user/tgcrm.service` |
| Исходники UI | `tam/web/index.src.html`, `styles.css`, `app.js`, `i18n.js` |
| Сборка UI | `tam/web/build.py` → `tam/web/index.html` (единый файл) |
| Локализация | `docs/I18N.md`, `tools/i18n_*.py`, `tools/i18n_glossary.md` |

## Обязательные правила

* `tam/web/index.html` — **сборка**. Правки только в `index.src.html` / `styles.css` /
  `app.js` / `i18n.js`, потом `python3 tam/web/build.py` и `systemctl --user restart tgcrm`.
* Новая строка интерфейса = новая строка локализации: см. `docs/I18N.md`
  (extract → перевод → `tools/i18n_build.py` → build). Иначе в UI останется китайский.
* Ключевой словарь `tam/web/i18n.data.js` генерируется, руками не правится.
  Ручные дополнения — `tools/i18n_extra.json`.
* Эмодзи в интерфейсе не использовать: иконки — SVG-спрайт (`#i-*`), на машинах без
  CJK/emoji-шрифтов эмодзи превращаются в «тофу».
* Секреты (`.env`, `TAM_MASTER_KEY`, токены, session-строки) — не логировать,
  не коммитить, не индексировать в RAG.

## Проверки «получилось»

```bash
systemctl --user is-active tgcrm                  # active
curl -s -o /dev/null -w '%{http_code}' localhost:8848   # 200
.venv/bin/python -m tam.cli doctor                # без ✗
python3 tools/i18n_validate.py                    # все батчи OK
```

UI: открыть `http://127.0.0.1:8848`, переключить RU/EN и тему, в консоли браузера
выполнить сниппет поиска остатков CJK из `docs/I18N.md` — должен вернуть пустой список.

## Что уже сделано поверх upstream

* Локализация RU/EN с переключателем в шапке (перевод на уровне DOM, `app.js` не переписан).
* Светлая/тёмная тема (CSS-переменные + `data-theme`), выбор запоминается.
* Эмодзи заменены инлайн-SVG (спрайт в начале `<body>`).
* `tools/i18n_*.py` — пайплайн извлечения/сборки/проверки словарей.

## Грабли

* `setup.py`/`requirements.txt` тянут `opentele`, который ломает Telethon — пакет удалён
  (`pip uninstall opentele`); tdata разбирает встроенный парсер.
* `python-telegram-bot` нужен только для `TAM_FRONTEND=bot`; для веб-режима не обязателен.
* systemd-юнит использует кириллический путь — в юните путь прописан целиком, не через `~`.
* Перезапуск сервиса рвёт активные задачи (рассылки/перегенерацию) — предупреждать.
