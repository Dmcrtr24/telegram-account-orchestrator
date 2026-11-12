---
name: tgcrm-deploy
description: Как развернуть/обновить self-hosted TAO (Telegram Account Orchestrator) на этой машине — venv, .env, doctor, systemd-юнит tgcrm, проверка порта и UI. Вызывай, когда просят развернуть tgcrm/«эту црмку», перезапустить после правок, поднять на другом порту, включить бота или переехать на другой путь.
whenToUse: развернуть tgcrm, обновить/перезапустить сервис, сменить порт, включить TAM_FRONTEND=bot, переустановить venv
---

# Развёртывание TAO (tgcrm) на локальной машине

## Что уже стоит

| Что | Значение |
|-----|----------|
| Каталог | `/home/golden/Проекты/tgcrm` |
| venv | `.venv` (Python 3.14), зависимости из `requirements.txt` |
| Сервис | `systemctl --user tgcrm` → `http://127.0.0.1:8848` |
| Юнит | `~/.config/systemd/user/tgcrm.service` |
| Конфиг | `.env` (генерируется `setup.py`), данные в `data/` |

## С нуля (новый каталог / переустановка)

```bash
cd /home/golden/Проекты/tgcrm
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip uninstall -y opentele     # ОБЯЗАТЕЛЬНО: ломает Telethon
.venv/bin/python setup.py --auto --deploy local --frontend web --skip-install --no-start --token
.venv/bin/python -m tam.cli doctor                # не должно быть ✗
```

`setup.py` создаёт `.env`, генерирует `TAM_MASTER_KEY` и `TAM_WEB_TOKEN` и печатает токен.
`--deploy server` = bind `0.0.0.0` + токен по умолчанию; `local` = только `127.0.0.1`.

## systemd-юнит (шаблон)

```ini
[Unit]
Description=tgcrm — Telegram Account Orchestrator (TAO web console, 127.0.0.1:8848)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/golden/Проекты/tgcrm
Environment=TAM_NO_MENU=1
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/golden/Проекты/tgcrm/.venv/bin/python -m tam.cli run --deploy local --frontend web --port 8848 --no-menu
Restart=on-failure
RestartSec=3
StandardOutput=append:/home/golden/Проекты/tgcrm/data/service.log
StandardError=append:/home/golden/Проекты/tgcrm/data/service.log

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload && systemctl --user enable --now tgcrm
systemctl --user status tgcrm --no-pager
```

## Проверка «получилось»

```bash
systemctl --user is-active tgcrm                                   # active
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8848/     # 200
TOKEN=$(grep '^TAM_WEB_TOKEN=' .env | cut -d= -f2)
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8848/api/stats   # {"total":N,...}
tail -20 data/service.log
```

UI: открыть адрес, вставить токен в поле «Токен доступа» (local-режим можно и без токена при
`TAM_NO_AUTH=1`), переключить RU/EN и тему.

## Грабли

* **`opentele`** из `requirements.txt` переопределяет Telethon и рвёт подключения — удалять после установки.
  tdata разбирает встроенный парсер (`tdata_native`), opentele нужен только для экспорта tdata.
* `python-telegram-bot` нужен только при `TAM_FRONTEND=bot|both`; для веб-режима не обязателен.
* Путь с кириллицей (`Проекты`) — в юните писать абсолютный путь, `~` не раскрывается.
* После правок фронтенда нужен `cd tam/web && python3 build.py` (собирает `index.html` из исходников),
  иначе сервер отдаст старый файл.
* `systemctl --user restart tgcrm` рвёт активные задачи (рассылки, перегенерацию сессий) — предупреждать.
* Смена `TAM_MASTER_KEY` = потеря всех сохранённых сессий. Бэкапить `.env`.
* Python 3.14: doctor предупреждает про tdata-импорт; если он реально падает — пересобрать venv на 3.12.
