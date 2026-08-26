# Agent handoff — coolify-telegram-proxy

## Status
Coolify project **telegram-proxy** with Git resource `alian1998/coolify-telegram-proxy` (Docker Compose).

- Project: http://88.222.213.240:8000/project/pkygix91rf28n7f7rpl1oges/environment/xd2odiyrbcrfxgmvvsm9kiqx
- App: http://88.222.213.240:8000/project/pkygix91rf28n7f7rpl1oges/environment/xd2odiyrbcrfxgmvvsm9kiqx/application/mk83t4mpfxuaiybh7baybz4m
- HTTP publish port **18080** (8080 occupied on VPS)
- **IP masking model:** bot → VPS proxy → Telegram; Telegram sees `88.222.213.240` only
- Optional `UPSTREAM_PROXY_*` for foreign exit (leave empty for own VPS IP)
- `Getway-support-autoworker/server/telegramBot.js` reads `TELEGRAM_HTTP_PROXY`

## Stack
- `proxy/` — 3proxy, HTTP + SOCKS5, optional upstream parent
- `dashboard/` — list UI, masked IP display, Telegram API check
- `examples/support-bot.env` — bot env template

## Env (Coolify)
- `PROXY_PASSWORD`, `DASHBOARD_PASSWORD`, `SESSION_SECRET`
- `PROXY_PUBLIC_HOST=88.222.213.240`
- `HTTP_PUBLISH_PORT=18080`, `SOCKS_PUBLISH_PORT=1080`, `DASHBOARD_PUBLISH_PORT=3000`
- `PROXY_COUNTRY=IN` (label only)

## Not done
- Push latest local changes + Coolify redeploy
- External probe: `18080` / `3000` not responding (containers down or firewall)
- Set `TELEGRAM_HTTP_PROXY=http://tgproxy:PASS@88.222.213.240:18080` on support bot app + redeploy

## Next
1. `git push` → Coolify redeploy telegram-proxy
2. Dashboard → Telegram API = OK
3. Bot Coolify env → `TELEGRAM_HTTP_PROXY` → redeploy bot
