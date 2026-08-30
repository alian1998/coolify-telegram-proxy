# Agent handoff — coolify-telegram-proxy

## Status (2026-08-30)

### Singapore Coolify (primary for Telegram exit) — IN PROGRESS
- Coolify: http://5.199.164.217:8000/ (v4.3.14, SG / Cherry Servers)
- Project: `telegram-proxy` → `afwfmmcfe8bfufji7bt6bho5`
- Env: `qnxbinpvqm0nisqbxzzufudz` (production)
- App UUID: `cxzbexuvcyihgafzfqv9vaw1`
- App UI: http://5.199.164.217:8000/project/afwfmmcfe8bfufji7bt6bho5/environment/qnxbinpvqm0nisqbxzzufudz/application/cxzbexuvcyihgafzfqv9vaw1
- Git: public temporarily → `alian1998/coolify-telegram-proxy` branch `main` @ `3750ee4`
- Compose path: `/docker-compose.yml`
- Destination: localhost Standalone Docker
- **Do not touch other projects** on this Coolify (jetx, b2c, etc.)

#### Deploy notes
- First deploy **Failed**: host port `8080` already allocated
- `HTTP_PUBLISH_PORT` set to **18080**
- Later deploys **Success**, but **proxy crash-loops** (dashboard can still briefly listen on `:3000`)
- **Root cause (Coolify terminal `docker logs`):** `log /dev/stdout D` → 3proxy tries `/dev/stdout.YYYY.MM.DD` → `Permission denied` → exit
- **Fix:** `proxy/entrypoint.sh` → use `log` without daily rotation (pushed; redeploy telegram-proxy only)
- Coolify UI: “Cannot connect to real-time service” (unusual UI/state)
- **Constraint:** never touch other Coolify projects/containers on this host

#### Credentials
Set only in Coolify env (do not commit): `PROXY_USERNAME`, `PROXY_PASSWORD`, `DASHBOARD_PASSWORD`, `SESSION_SECRET`.
Public host `5.199.164.217`, ports HTTP `18080` / SOCKS `1080` / dashboard `3000`.

#### Next on SG
1. Push entrypoint log fix → Coolify **telegram-proxy only** redeploy
2. Confirm status **Running**; probe `:18080` / `:1080` / `:3000/health`
3. Re-private GitHub repo if still public
4. Wire bot later: `TELEGRAM_HTTP_PROXY=http://USER:PASS@5.199.164.217:18080`

### Mumbai Coolify (older) — separate
- http://88.222.213.240:8000/project/pkygix91rf28n7f7rpl1oges/environment/xd2odiyrbcrfxgmvvsm9kiqx
- HTTP publish **18080**, `PROXY_PUBLIC_HOST=88.222.213.240`, country label IN

## Stack
- `proxy/` — 3proxy, HTTP + SOCKS5, optional upstream parent
- `dashboard/` — list UI, masked IP display, Telegram API check
- `examples/support-bot.env` — bot env template

## Related
- `Getway-support-autoworker/server/telegramBot.js` reads `TELEGRAM_HTTP_PROXY` (not wired to SG proxy yet)
