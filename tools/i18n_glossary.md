# i18n glossary — TAO web console (zh-CN → ru / en)

Project: self-hosted Telegram multi-account manager (TAO). UI is a single-page console.
Tone: compact UI strings, no fluff. Buttons = infinitive in Russian ("Обновить"), nouns for labels.

## Do not translate (keep verbatim)
Telegram, Telethon, TDesktop, MTProto, tdata, StringSession, session, .session, API, REST, JSON, NDJSON,
CSV, ZIP, SQLite, HTTPS, proxy(→ прокси), SpamBot, OKPay, Premium, Passcode, Base, Key, Token(→ токен),
OpenAI, Claude, Gemini, Azure, DeepSeek, Grok, Moonshot, Ollama, OneAPI, NewAPI, BotFather, Windows, macOS,
Linux, Docker, systemd, env var names (TAM_*), URLs, file names, values in `backticks`.

## Glossary (Russian)
账号 аккаунт · 号 аккаунт · 号包 пакет аккаунтов · 会话 сессия · 登录 вход/войти · 退出登录 выход ·
踢设备 / 清设备 сброс других устройств · 二验 / 两步验证 2FA (двухфакторная аутентификация) ·
取码链接 ссылка для получения кода · 自动登录 автовход · 扫码登录 вход по QR · 重生会话 перегенерация сессии ·
防找回 защита от восстановления · 批量 пакетно / массово · 群发 рассылка · 线索 лиды · 任务 задача ·
任务中心 центр задач · 采集发言人 сбор активных участников · 代理 прокси · 标签 теги · 别名 метка ·
状态 статус · 健康检查 проверка работоспособности · 筛活 проверка активности · 授权 авторизация ·
令牌 токен · 主密钥 мастер-ключ · 工具箱 инструменты · 参数面板 параметры · 热重载 горячая перезагрузка ·
一键体检 диагностика · 布局 раскладка · 群组 группа · 频道 канал · 二维码 QR-код · 养号 прогрев аккаунта ·
封禁 заблокирован · 受限 ограничен · 未登录 не авторизован · 正常 активен · 删除 удалить · 导入 импорт ·
导出 экспорт · 试运行 пробный запуск · 帮助 справка · 刷新 обновить · 保存 сохранить · 取消 отмена ·
确定 OK · 设置 настройки · 权限 права · 上游 провайдер · 对话 диалог · 线索库 база лидов ·
通讯录 контакты · 隐私 конфиденциальность · 屏蔽 заблокировать пользователя · 解封 разблокировать

## Glossary (English)
账号 account · 会话 session · 登录 sign in · 退出登录 sign out · 踢设备/清设备 terminate other devices ·
二验/两步验证 2FA · 取码链接 code-retrieval link · 号包 account pack · 批量 bulk · 群发 broadcast ·
线索 leads · 任务 task · 采集发言人 collect active members · 代理 proxy · 标签 tags · 别名 label ·
健康检查 health check · 筛活 liveness check · 令牌 token · 主密钥 master key · 工具箱 toolbox ·
参数面板 settings · 热重载 hot reload · 一键体检 doctor · 布局 layout · 群组 group · 频道 channel ·
养号 warm-up · 封禁 banned · 受限 restricted · 未登录 unauthorized · 正常 active

## Mechanics
- `%s` placeholders (kind=pattern): keep the SAME count and order.
- Preserve leading/trailing spaces and separators (` · `, ` | `, `：`→`: `, `，`→`, `, `。`→`.`).
- Chinese quotes “…” → «…» (ru) / “…” (en). Keep emoji/arrows as-is unless noted.
- Empty or punctuation-only strings: return an equivalent, do not invent content.
