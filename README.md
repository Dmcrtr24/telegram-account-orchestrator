<div align="center">
  <img src="docs/assets/tao-icon.png" width="140" alt="TAO">
</div>

# Telegram Account Orchestrator

Self-hosted менеджер Telegram-аккаунтов: веб-консоль, CLI, Telegram-бот, REST API и MCP.
Сессии хранятся зашифрованными в локальной SQLite, наружу ничего не уходит.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Telethon](https://img.shields.io/badge/telethon-MTProto-2CA5E0.svg)](https://github.com/LonamiWebs/Telethon)

<img src="docs/assets/screenshot-dark-ru.png" width="900" alt="Веб-консоль: русский интерфейс, тёмная тема">

## Что это

Форк [soulknight666/telegram-account-orchestrator](https://github.com/soulknight666/telegram-account-orchestrator)
с русским интерфейсом. Вся функциональность — из апстрима: код приложения, API и логика работы
не переписаны, добавлена локализация.

База — **v0.3.2** (интерфейс «Workspace»): автор выложил её только в релизных архивах, в git
оставалась 0.3.1, поэтому исходники v0.3.2 перенесены сюда вручную.

Подходит, когда аккаунтов много и ими нужно управлять с одной панели: импорт, проверка
работоспособности, сброс чужих устройств, 2FA, массовые операции, работа с пакетами аккаунтов.

## Возможности

**Управление аккаунтами**

- Импорт: `.session`, StringSession, `tdata` (встроенный парсер, opentele не нужен), списки номеров
- Вход по коду, по ссылке для получения кода и по QR-коду с телефона
- Шифрование сессий (Fernet) в SQLite, мастер-ключ в `.env`
- Проверка работоспособности, статусы (активен / ограничен / забанен / не авторизован), SpamBot
- Сброс других устройств с проверкой и повторами; период настраивается на каждый аккаунт
- 2FA: статус, смена пароля, официальный сброс, привязка почты

**Массовые операции**

- Пакетная проверка, автовход, рассылка с вариантами текста, прогрев, теги, экспорт
- Перегенерация сессий с новым отпечатком устройства (защита от восстановления аккаунта)
- Центр задач с прогрессом и остановкой, база лидов, сбор активных участников групп

**Пакеты аккаунтов (ZIP)**

- Распаковка, объединение, сортировка по дате регистрации, конвертация Session ↔ tdata, Passkey

**Интерфейсы**

- Веб-консоль, CLI (`python -m tam.cli`), REST API, MCP-сервер, Telegram-бот
- AI-помощник в панели: работает с аккаунтами через инструменты, с ограничениями по правам

**Что добавлено в этом форке**

- Русский и английский интерфейс, переключатель `RU / EN` в шапке, выбор запоминается
  в браузере; переведено 3341 строка и 186 шаблонов — панели, таблицы, диалоги, подсказки,
  справка, описания инструментов и параметров, ошибки API
- Перевод применяется на уровне DOM отдельным словарём: исходные строки остаются китайскими
  (msgid), `app.js` не переписан, обновления апстрима переносятся легче
- Светлая и тёмная тема — штатная возможность v0.3.2 (кнопка ☀/🌙 в шапке)
- `?token=<токен>` в URL: токен сохраняется и вычищается из адресной строки — удобно для ярлыка
  или киоск-режима на сервере

## Установка

Нужен Python 3.10+.

```bash
git clone https://github.com/Dmcrtr24/telegram-account-orchestrator.git
cd telegram-account-orchestrator

python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip uninstall -y opentele      # обязательно: переопределяет Telethon

.venv/bin/python setup.py --auto --deploy local --frontend web --token
```

`setup.py` создаст `.env`, сгенерирует мастер-ключ и токен доступа, проведёт диагностику
и запустит консоль на `http://127.0.0.1:8848`. Токен печатается в конце — его нужно вставить
в поле «Токен доступа» в шапке (или открыть `http://127.0.0.1:8848/?token=<токен>`).

Дальше: «Диагностика» → импорт аккаунтов → проверка работоспособности.

### Автозапуск (systemd, Linux)

```ini
[Unit]
Description=TAO — Telegram Account Orchestrator
After=network-online.target

[Service]
WorkingDirectory=/path/to/telegram-account-orchestrator
Environment=TAM_NO_MENU=1
ExecStart=/path/to/telegram-account-orchestrator/.venv/bin/python -m tam.cli run --deploy local --frontend web --no-menu
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now tao.service
```

## Настройка

Всё в `.env`; часть параметров меняется из панели «Параметры».

| Переменная | Назначение |
|---|---|
| `TAM_MASTER_KEY` | Шифрование сессий. Потеря = потеря всех аккаунтов |
| `TAM_WEB_TOKEN` | Токен доступа к консоли и API |
| `TAM_DEPLOY` | `local` (только 127.0.0.1) или `server` (0.0.0.0, нужен HTTPS-прокси) |
| `TAM_FRONTEND` | `web`, `bot` или `both` |
| `TAM_API_ID` / `TAM_API_HASH` | Нужны для входа по номеру; для импорта session/tdata не обязательны |
| `TAM_DEFAULT_PROXY` | Прокси по умолчанию, `socks5://user:pass@host:1080` |
| `TAM_BATCH_CONCURRENCY` | Параллельность массовых операций (1–32) |

Перед публикацией наружу: `TAM_DEPLOY=server`, сильный `TAM_WEB_TOKEN`, HTTPS-реверс-прокси,
бэкап `.env`.

## Документация

- [`docs/I18N.md`](docs/I18N.md) — как устроен перевод, как добавить строки, темы
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — развёртывание (апстрим)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — архитектура (апстрим)
- [`README.zh-CN.md`](README.zh-CN.md) — полная документация апстрима (китайский)
- [`FOR_AI.md`](FOR_AI.md) — руководство для разработки и агентов (апстрим)

## Лицензия

MIT — см. [LICENSE](LICENSE). Часть кода пакетной обработки (`tam/gaf/`) перенесена из
[GAFBot](https://github.com/kugua332334554/GAFBot) под MIT, см. [NOTICE.GAFBot](NOTICE.GAFBot).

## Благодарности

Основа — [soulknight666/telegram-account-orchestrator](https://github.com/soulknight666/telegram-account-orchestrator)
(MIT). Этот репозиторий — форк с локализацией; баги самого приложения логично проверять на апстриме.
